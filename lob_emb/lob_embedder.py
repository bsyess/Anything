"""
LOB -> embedding encoder (one time-index = 10 one-minute snapshots).

Raw layout per snapshot: 404 = 4 snapshot scalars + 2 sides * (10 features * 20 levels).

    raw[..., 0]       : open price            (today's open)
    raw[..., 1]       : mid price             (at snapshot time)
    raw[..., 2]       : cumulative trade vol  (today, in shares)
    raw[..., 3]       : total float shares
    raw[..., 4:204]   : ASK side, feature-major:
                        p1..p20, v1..v20, c1..c20, hhi1..20, age1..20,
                        nr1..20, hv1..20, wp1..20, cv1..20, bt1..20
    raw[..., 204:404] : BID side, same feature order

If your layout differs (e.g. bid before ask, or level-major), only
`_parse_raw` needs to change.

Input : raw [..., 10, 404]   (leading dims are typically [batch] or [batch, T])
Output : emb [..., d_out], lob_valid [...] (1.0 if the ti has any real LOB data)

Missing data (LOB history shorter than factor history -> all-zero snapshots):
  * invalid snapshots are replaced by a learned [MISS] token (which still
    receives the intra-ti positional embedding);
  * a fully missing ti therefore maps to a *learned* null embedding, not to
    the zero vector, and `lob_valid` is returned so the downstream model can
    additionally condition on availability (recommended: concat it alongside
    the embedding).
"""

import math
from dataclasses import dataclass

import torch
import torch.nn as nn

RAW_DIM = 404
N_LVL = 20
N_RAW_FEAT = 10          # p v c hhi age nr hv wp cv bt
N_LVL_FEAT = 13          # engineered per-level features (see _build_features)
N_SNAP_FEAT = 10         # engineered per-snapshot scalar features
EPS = 1e-6


@dataclass
class LOBConfig:
    n_snaps: int = 10          # snapshots per ti
    d_level: int = 64          # token width in the book (level) encoder
    n_book_queries: int = 8    # learned inducing queries pooling the book
    n_level_heads: int = 4
    d_scalar: int = 32         # width of the snapshot-scalar branch
    d_snap: int = 128          # snapshot vector width (= time encoder width)
    n_time_layers: int = 2
    n_time_heads: int = 4
    d_out: int = 128           # final embedding dim (concat target)
    dropout: float = 0.1
    aux_head: bool = True      # auxiliary next-minute mid-return prediction


class LOBEmbedder(nn.Module):
    def __init__(self, cfg: LOBConfig = LOBConfig()):
        super().__init__()
        self.cfg = cfg
        d, dt = cfg.d_level, cfg.d_snap

        # ---- stage 1: per-snapshot book encoder ----
        self.level_in = nn.Sequential(
            nn.LayerNorm(N_LVL_FEAT),
            nn.Linear(N_LVL_FEAT, d),
            nn.GELU(),
            nn.Linear(d, d),
        )
        # continuous positional encoding from relative price (multi-scale
        # Fourier features of the compressed distance-to-mid), so "position"
        # means price distance, not level rank; rank embedding is auxiliary
        self.register_buffer("pe_freqs",
                             torch.tensor([1.0, 2.0, 4.0, 8.0, 16.0]) * math.pi)
        self.price_pos = nn.Linear(10, d, bias=False)
        self.side_level_pos = nn.Parameter(torch.randn(2, N_LVL, d) * 0.02)

        # inducing-point book pooling: K learned queries cross-attend over the
        # 40 level tokens (plus one never-masked sentinel) -> K summaries
        self.book_queries = nn.Parameter(torch.randn(cfg.n_book_queries, d) * 0.02)
        self.null_level = nn.Parameter(torch.randn(d) * 0.02)
        self.book_attn = nn.MultiheadAttention(
            d, cfg.n_level_heads, dropout=cfg.dropout, batch_first=True)
        self.book_merge = nn.Sequential(
            nn.LayerNorm(cfg.n_book_queries * d),
            nn.Linear(cfg.n_book_queries * d, 2 * d),
            nn.GELU(),
            nn.Linear(2 * d, d),
        )

        # ---- snapshot-scalar branch ----
        self.scalar_mlp = nn.Sequential(
            nn.LayerNorm(N_SNAP_FEAT),
            nn.Linear(N_SNAP_FEAT, cfg.d_scalar),
            nn.GELU(),
        )
        self.snap_proj = nn.Linear(d + cfg.d_scalar, dt)

        # ---- stage 2: intra-ti temporal encoder (10 minute snapshots) ----
        self.miss_token = nn.Parameter(torch.randn(dt) * 0.02)
        self.time_pos = nn.Parameter(torch.randn(cfg.n_snaps, dt) * 0.02)
        self.ti_cls = nn.Parameter(torch.randn(dt) * 0.02)
        self.time_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=dt, nhead=cfg.n_time_heads, dim_feedforward=2 * dt,
                dropout=cfg.dropout, batch_first=True, norm_first=True,
                activation="gelu",
            ),
            num_layers=cfg.n_time_layers,
            enable_nested_tensor=False,
        )

        # ---- output head ----
        self.head = nn.Linear(2 * dt, cfg.d_out)
        self.out_norm = nn.LayerNorm(cfg.d_out)
        # keep the LOB branch quiet at init so it does not disturb the
        # mature factor backbone early in training
        with torch.no_grad():
            self.head.weight.mul_(0.1)
            self.head.bias.zero_()

        self.aux_head = (
            nn.Linear(dt, 1) if cfg.aux_head else None
        )

    # ------------------------------------------------------------------ #
    # parsing & feature engineering (pure tensor ops, no parameters)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_raw(x: torch.Tensor):
        """x: [B, S, 404] -> scalars [B,S,4], book [B,S,2,20,10] (ask=0, bid=1)."""
        B, S, _ = x.shape
        scalars = x[..., :4]
        ask = x[..., 4:204].reshape(B, S, N_RAW_FEAT, N_LVL)
        bid = x[..., 204:404].reshape(B, S, N_RAW_FEAT, N_LVL)
        book = torch.stack([ask, bid], dim=2)          # [B,S,2,10,20]
        book = book.permute(0, 1, 2, 4, 3).contiguous()  # [B,S,2,20,10]
        return scalars, book

    @staticmethod
    def _build_features(x: torch.Tensor):
        """
        x: [B, S, 404] raw.
        Returns:
            lvl_feats    [B,S,2,20,N_LVL_FEAT]  per-level features, 0 where invalid
            lvl_valid    [B,S,2,20] bool
            snap_scalars [B,S,N_SNAP_FEAT]      per-snapshot features, 0 where invalid
            snap_valid   [B,S] bool
        """
        scalars, book = LOBEmbedder._parse_raw(x)
        open_p, mid, cumv, flt = scalars.unbind(-1)            # [B,S]
        p, v, c, hhi, age, nr, hv, wp, cv, bt = book.unbind(-1)  # [B,S,2,20]

        snap_valid = (mid > 0) & (flt > 0)
        safe_mid = torch.where(snap_valid, mid, torch.ones_like(mid))
        safe_flt = torch.where(snap_valid, flt, torch.ones_like(flt))
        safe_open = torch.where(open_p > 0, open_p, safe_mid)

        mid_e = safe_mid[..., None, None]
        flt_e = safe_flt[..., None, None]
        lvl_valid = (v > 0) & snap_valid[..., None, None]

        # --- per-level features, all roughly O(1) and scale-free -----------
        rel_bps = (p - mid_e) / mid_e * 1e4                   # signed distance to mid
        rel = torch.sign(rel_bps) * torch.log1p(rel_bps.abs()) / 8.0
        log_v = torch.log1p(v / flt_e * 1e4) / 5.0            # vol as bps of float
        side_sum = v.sum(-1, keepdim=True)
        shape = v / (side_sum + EPS)                          # within-side shape
        cumshape = torch.cumsum(shape, dim=-1)                # cumulative depth profile
        log_c = torch.log1p(c.clamp_min(0)) / 5.0
        hhi_n = hhi.clamp(0, 1)
        age_n = torch.log1p(age.clamp_min(0)) / math.log1p(14400.0)
        nr_n = nr.clamp(0, 1)
        hv_frac = (hv / (v + EPS)).clamp(0, 1)                # front-order dominance
        wp_n = torch.log1p(wp.clamp_min(0)) / 5.0
        cv_rel = torch.log1p(cv.clamp_min(0) / (v + 1.0)) / 3.0  # cancel intensity
        bt_n = torch.log1p(bt.clamp_min(0)) / 4.0

        lvl_feats = torch.stack(
            [rel, log_v, shape, cumshape, log_c, hhi_n, age_n, nr_n,
             hv_frac, wp_n, cv_rel, bt_n, lvl_valid.float()],
            dim=-1,
        )
        lvl_feats = lvl_feats * lvl_valid[..., None]

        # --- per-snapshot scalar features ----------------------------------
        a1p, b1p = p[..., 0, 0], p[..., 1, 0]
        a1v, b1v = v[..., 0, 0], v[..., 1, 0]
        bbo_valid = (a1v > 0) & (b1v > 0)
        spread = torch.log1p(((a1p - b1p) / safe_mid * 1e4).clamp_min(0)) / 8.0
        spread = spread * bbo_valid
        micro = (a1p * b1v + b1p * a1v) / (a1v + b1v + EPS)
        micro_bps = (micro - safe_mid) / safe_mid * 1e4
        micro_dev = torch.sign(micro_bps) * torch.log1p(micro_bps.abs()) / 8.0
        micro_dev = micro_dev * bbo_valid

        va, vb = v[..., 0, :], v[..., 1, :]                   # [B,S,20]
        imb_all = (vb.sum(-1) - va.sum(-1)) / (vb.sum(-1) + va.sum(-1) + EPS)
        imb_top5 = (vb[..., :5].sum(-1) - va[..., :5].sum(-1)) / (
            vb[..., :5].sum(-1) + va[..., :5].sum(-1) + EPS)
        depth = torch.log1p((va.sum(-1) + vb.sum(-1)) / safe_flt * 1e4) / 5.0

        ret_open = (safe_mid.log() - safe_open.log()).clamp(-0.3, 0.3) * 10.0

        # minute-over-minute deltas within the ti (first minute -> 0)
        dvol = torch.diff(cumv, dim=1, prepend=cumv[:, :1])
        traded = torch.log1p(dvol.clamp_min(0) / safe_flt * 1e4) / 5.0
        turnover = torch.log1p((cumv / safe_flt).clamp_min(0) * 100.0) / 5.0
        log_mid = safe_mid.log()
        dmid = torch.diff(log_mid, dim=1, prepend=log_mid[:, :1])
        prev_valid = torch.cat([snap_valid[:, :1] & False,
                                snap_valid[:, :-1]], dim=1)
        dmid = (dmid * 100.0).clamp(-3, 3) * (snap_valid & prev_valid)

        snap_scalars = torch.stack(
            [ret_open, spread, micro_dev, imb_all, imb_top5, depth,
             traded, turnover, dmid, snap_valid.float()],
            dim=-1,
        )
        snap_scalars = snap_scalars * snap_valid[..., None]

        # per-snapshot mid log-return to the NEXT minute (aux target)
        fwd_ret = torch.diff(log_mid, dim=1, append=log_mid[:, -1:]) * 100.0
        next_valid = torch.cat([snap_valid[:, 1:],
                                snap_valid[:, -1:] & False], dim=1)
        aux_mask = snap_valid & next_valid

        return lvl_feats, lvl_valid, snap_scalars, snap_valid, fwd_ret, aux_mask

    # ------------------------------------------------------------------ #
    def _encode(self, raw: torch.Tensor):
        cfg = self.cfg
        lead = raw.shape[:-2]
        S = raw.shape[-2]
        assert S == cfg.n_snaps and raw.shape[-1] == RAW_DIM
        x = raw.reshape(-1, S, RAW_DIM).float()
        B = x.shape[0]

        (lvl_feats, lvl_valid, snap_scalars,
         snap_valid, fwd_ret, aux_mask) = self._build_features(x)

        # ---- stage 1: book pooling via K learned cross-attention queries ----
        h = self.level_in(lvl_feats)                      # [B,S,2,20,d]
        rel = lvl_feats[..., 0]                           # compressed rel price
        ang = rel.unsqueeze(-1) * self.pe_freqs           # [B,S,2,20,5]
        pe = self.price_pos(torch.cat([ang.sin(), ang.cos()], dim=-1))
        h = h + pe + self.side_level_pos                  # price- + rank-position
        kv = h.reshape(B * S, 2 * N_LVL, cfg.d_level)
        kv = torch.cat(
            [self.null_level.expand(B * S, 1, cfg.d_level), kv], dim=1)
        pad = torch.cat(
            [torch.zeros(B * S, 1, dtype=torch.bool, device=kv.device),
             ~lvl_valid.reshape(B * S, 2 * N_LVL)],
            dim=1,
        )                                                  # sentinel never masked
        q = self.book_queries.expand(B * S, -1, -1)
        summ, _ = self.book_attn(q, kv, kv, key_padding_mask=pad,
                                 need_weights=False)       # [B*S, K, d]
        book_vec = self.book_merge(summ.flatten(1)).reshape(B, S, cfg.d_level)

        # ---- fuse with snapshot scalars -> snapshot vector ----
        snap = self.snap_proj(
            torch.cat([book_vec, self.scalar_mlp(snap_scalars)], dim=-1)
        )                                                  # [B,S,d_snap]

        # ---- missing snapshots -> learned token (keeps position info) ----
        snap = torch.where(snap_valid[..., None], snap,
                           self.miss_token.expand_as(snap))
        snap_in = snap + self.time_pos                     # [B,S,d_snap]

        # ---- stage 2: temporal encoder over the 10 minutes ----
        tcls = self.ti_cls.expand(B, 1, cfg.d_snap)
        z = self.time_encoder(torch.cat([tcls, snap_in], dim=1))
        emb = self.head(torch.cat([z[:, 0], z[:, 1:].mean(dim=1)], dim=-1))
        emb = self.out_norm(emb)

        lob_valid = snap_valid.any(dim=1).float()
        return emb, lob_valid, snap, fwd_ret, aux_mask, lead

    def forward(self, raw: torch.Tensor):
        """raw [..., 10, 404] -> emb [..., d_out], lob_valid [...]."""
        emb, lob_valid, _, _, _, lead = self._encode(raw)
        return emb.reshape(*lead, self.cfg.d_out), lob_valid.reshape(*lead)

    def forward_with_aux(self, raw: torch.Tensor):
        """
        Same as forward, plus an auxiliary MSE loss: predict next-minute
        mid log-return (x100) from each (pre-temporal) snapshot vector.
        Add `lambda * aux_loss` (e.g. lambda=0.1) to the main objective to
        regularize the LOB branch, especially useful early in training.
        """
        assert self.aux_head is not None
        emb, lob_valid, snap, fwd_ret, aux_mask, lead = self._encode(raw)
        pred = self.aux_head(snap).squeeze(-1)             # [B,S]
        m = aux_mask.float()
        aux_loss = ((pred - fwd_ret) ** 2 * m).sum() / m.sum().clamp_min(1.0)
        return (emb.reshape(*lead, self.cfg.d_out),
                lob_valid.reshape(*lead), aux_loss)
