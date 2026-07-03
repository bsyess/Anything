# -*- coding: utf-8 -*-
import torch
import torch.nn as nn
import torch.nn.functional as F


class MlpBlock(nn.Module):
    def __init__(self, nipt, nmlp):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(nipt, nmlp),
            nn.GELU(),
            nn.Linear(nmlp, nipt),
        )

    def forward(self, x):
        return self.mlp(x)


class MixerBlock(nn.Module):
    """
    Plain MLP-Mixer block.

    x: [B, T, C]
    tmix: mix along time dimension
    cmix: mix along channel/factor dimension
    """
    def __init__(self, nipt, nslen, nthid, nchid):
        super().__init__()
        self.ln_t = nn.LayerNorm(nipt)
        self.tmix = MlpBlock(nslen, nthid)

        self.ln_c = nn.LayerNorm(nipt)
        self.cmix = MlpBlock(nipt, nchid)

    def forward(self, x):
        out = self.ln_t(x).permute(0, 2, 1)   # [B, C, T]
        x = x + self.tmix(out).permute(0, 2, 1)

        out = self.ln_c(x)
        x = x + self.cmix(out)

        return x


class MultiGroupFiLM(nn.Module):
    """
    Grouped / multi-branch FiLM.

    hf_repr: [B, D]
    lf_repr: [B, D]

    return:
        lf_mod:    [B, D]
        group_w:   [B, K]
        gamma_all: [B, K, D]
        beta_all:  [B, K, D]
    """
    def __init__(self, repr_dim, film_hidden=256, num_groups=3, p=0.0):
        super().__init__()
        self.num_groups = num_groups

        self.group_films = nn.ModuleList([
            nn.Sequential(
                nn.Linear(repr_dim, film_hidden),
                nn.GELU(),
                nn.Dropout(p=p),
                nn.Linear(film_hidden, repr_dim * 2),
            )
            for _ in range(num_groups)
        ])

        self.group_router = nn.Sequential(
            nn.Linear(repr_dim, film_hidden),
            nn.GELU(),
            nn.Dropout(p=p),
            nn.Linear(film_hidden, num_groups),
        )

    def forward(self, hf_repr, lf_repr, film_scale=0.3):
        gamma_list = []
        beta_list = []
        lf_mod_list = []

        for film in self.group_films:
            gamma_beta = film(hf_repr)
            gamma, beta = gamma_beta.chunk(2, dim=-1)

            gamma_list.append(gamma)
            beta_list.append(beta)

            lf_mod = (1.0 + film_scale * gamma) * lf_repr + film_scale * beta
            lf_mod_list.append(lf_mod)

        gamma_all = torch.stack(gamma_list, dim=1)      # [B, K, D]
        beta_all = torch.stack(beta_list, dim=1)        # [B, K, D]
        lf_mod_all = torch.stack(lf_mod_list, dim=1)    # [B, K, D]

        group_logits = self.group_router(hf_repr)
        group_w = torch.softmax(group_logits, dim=-1)   # [B, K]

        lf_mod = (lf_mod_all * group_w.unsqueeze(-1)).sum(dim=1)
        return lf_mod, group_w, gamma_all, beta_all


class DynamicLFRelationGroupedCR(nn.Module):
    """
    Plain HF MLP-Mixer + dynamic LF current/delta correction.

    Input:
        x: [B, slen, ninp]
        first n_lf_input dims: LF
        remaining dims: HF
    """

    def __init__(
        self,
        ninp,
        nhead,          # compatibility only, unused
        nhid,           # compatibility only, unused as unique width
        nlayers,
        p,
        slen,
        nopt,
        n_lf_input,

        hf_tnhid=128,
        hf_cnhid=256,
        hf_repr_dim=160,

        lf_hidden=512,
        head_hidden=256,
        router_hidden=128,
        film_hidden=256,
        relation_hidden=64,

        num_film_groups=3,
        skip_last_lf=9,
        film_scale=0.3,
        diff_scale=1.0,
        mask_threshold=1e-8,

        use_relation_in_router=True,
        use_relation_in_expert_x=True,
        use_relation_in_group_router=False,
    ):
        super().__init__()

        self.n_lf = int(n_lf_input)
        self.n_hf = int(ninp) - int(n_lf_input)
        self.slen = int(slen)
        self.nopt = int(nopt)

        self.skip_last_lf = int(skip_last_lf)
        self.film_scale = float(film_scale)
        self.diff_scale = float(diff_scale)
        self.mask_threshold = float(mask_threshold)

        self.use_relation_in_router = bool(use_relation_in_router)
        self.use_relation_in_expert_x = bool(use_relation_in_expert_x)
        self.use_relation_in_group_router = bool(use_relation_in_group_router)

        if self.n_hf <= 0:
            raise ValueError(f"ninp={ninp}, n_lf_input={n_lf_input}, got n_hf={self.n_hf} <= 0")

        if self.skip_last_lf < 0 or self.skip_last_lf >= self.n_lf:
            raise ValueError(f"skip_last_lf={skip_last_lf} invalid for n_lf_input={n_lf_input}")

        self.use_lf_dim = self.n_lf - self.skip_last_lf
        self.dynamic_lf_dim = self.use_lf_dim * 4

        self.hf_repr_dim = int(hf_repr_dim)
        self.relation_dim = 4
        self.num_film_groups = int(num_film_groups)

        self._last_a_lf = None
        self._last_a_x = None
        self._last_stats = {}

        # ===== HF backbone: plain MLP-Mixer =====
        self.hf_mlps = nn.Sequential(
            *[
                MixerBlock(self.n_hf, self.slen, hf_tnhid, hf_cnhid)
                for _ in range(nlayers)
            ]
        )

        self.hf_decode = nn.Sequential(
            nn.LayerNorm(self.n_hf),
            nn.Linear(self.n_hf, self.hf_repr_dim),
            nn.GELU(),
            nn.Dropout(p=p),
        )

        # ===== LF encoder: current + diff + update mask + age =====
        self.lf_encoder = nn.Sequential(
            nn.LayerNorm(self.dynamic_lf_dim),
            nn.Linear(self.dynamic_lf_dim, lf_hidden),
            nn.GELU(),
            nn.Dropout(p=p),
            nn.Linear(lf_hidden, self.hf_repr_dim),
            nn.GELU(),
            nn.Dropout(p=p),
        )

        # ===== relation projector =====
        self.relation_proj = nn.Sequential(
            nn.Linear(self.relation_dim, relation_hidden),
            nn.GELU(),
            nn.Dropout(p=p),
            nn.Linear(relation_hidden, relation_hidden),
            nn.GELU(),
        )

        # ===== base HF prediction =====
        self.expert_hf = nn.Sequential(
            nn.Linear(self.hf_repr_dim, head_hidden),
            nn.GELU(),
            nn.Dropout(p=p),
            nn.Linear(head_hidden, nopt),
        )

        # ===== grouped FiLM =====
        self.grouped_film = MultiGroupFiLM(
            repr_dim=self.hf_repr_dim,
            film_hidden=film_hidden,
            num_groups=self.num_film_groups,
            p=p,
        )

        # group-specific LF residual heads
        self.group_expert_lf = nn.ModuleList([
            nn.Sequential(
                nn.Linear(self.hf_repr_dim, head_hidden),
                nn.GELU(),
                nn.Dropout(p=p),
                nn.Linear(head_hidden, nopt),
            )
            for _ in range(self.num_film_groups)
        ])

        # interaction correction
        expert_x_in_dim = self.hf_repr_dim * 4
        if self.use_relation_in_expert_x:
            expert_x_in_dim += relation_hidden

        self.expert_x = nn.Sequential(
            nn.Linear(expert_x_in_dim, head_hidden),
            nn.GELU(),
            nn.Dropout(p=p),
            nn.Linear(head_hidden, nopt),
        )

        # router for LF correction and interaction correction
        router_in_dim = self.hf_repr_dim
        if self.use_relation_in_router:
            router_in_dim += relation_hidden

        self.router = nn.Sequential(
            nn.Linear(router_in_dim, router_hidden),
            nn.GELU(),
            nn.Dropout(p=p),
            nn.Linear(router_hidden, 2),
        )

        nn.init.constant_(self.router[-1].bias, -1.5)
        nn.init.normal_(self.router[-1].weight, std=0.01)

        if self.use_relation_in_group_router:
            self.group_router_refine = nn.Sequential(
                nn.Linear(self.num_film_groups + relation_hidden, film_hidden),
                nn.GELU(),
                nn.Dropout(p=p),
                nn.Linear(film_hidden, self.num_film_groups),
            )
        else:
            self.group_router_refine = None

    def _compute_age_feature(self, x_lf_seq):
        """
        For each LF feature, estimate how recently it changed.
        x_lf_seq: [B, T, D]
        return: [B, D]
        """
        B, T, D = x_lf_seq.shape
        if T <= 1:
            return x_lf_seq.new_zeros(B, D)

        diffs = torch.abs(x_lf_seq[:, 1:, :] - x_lf_seq[:, :-1, :])
        changed = (diffs > self.mask_threshold).float()

        changed_rev = torch.flip(changed, dims=[1])
        idx = torch.arange(T - 1, device=x_lf_seq.device, dtype=x_lf_seq.dtype).view(1, T - 1, 1)
        big = x_lf_seq.new_full((B, T - 1, D), float(T - 1))

        dist = torch.where(changed_rev > 0, idx.expand_as(changed_rev), big)
        min_dist = dist.min(dim=1).values

        age_feat = min_dist / max(T - 1, 1)
        return age_feat

    def _build_dynamic_lf_input(self, x_lf_seq):
        """
        x_lf_seq: [B, T, use_lf_dim]

        return:
            [current, diff1, upd_mask, age_feat]
        """
        current = x_lf_seq[:, -1, :]

        if x_lf_seq.size(1) >= 2:
            prev = x_lf_seq[:, -2, :]
        else:
            prev = torch.zeros_like(current)

        diff1 = self.diff_scale * (current - prev)
        upd_mask = (torch.abs(current - prev) > self.mask_threshold).float()
        age_feat = self._compute_age_feature(x_lf_seq)

        dyn_lf = torch.cat([current, diff1, upd_mask, age_feat], dim=-1)
        return dyn_lf

    def _build_relation_summary(self, hf_repr, lf_repr):
        eps = 1e-8

        cos_sim = F.cosine_similarity(hf_repr, lf_repr, dim=-1, eps=eps).unsqueeze(-1)
        norm_gap = torch.norm(hf_repr - lf_repr, dim=-1, keepdim=True)
        dot_scaled = (hf_repr * lf_repr).sum(dim=-1, keepdim=True) / (hf_repr.size(-1) ** 0.5)
        abs_diff_mean = torch.mean(torch.abs(hf_repr - lf_repr), dim=-1, keepdim=True)

        raw_relation = torch.cat(
            [cos_sim, norm_gap, dot_scaled, abs_diff_mean],
            dim=-1,
        )

        rel_feat = self.relation_proj(raw_relation)
        return raw_relation, rel_feat

    def _build_expert_x_input(self, hf_repr, lf_repr, rel_feat=None):
        x = torch.cat(
            [
                hf_repr,
                lf_repr,
                hf_repr * lf_repr,
                hf_repr - lf_repr,
            ],
            dim=-1,
        )

        if self.use_relation_in_expert_x and rel_feat is not None:
            x = torch.cat([x, rel_feat], dim=-1)

        return x

    def _build_router_input(self, hf_repr, rel_feat=None):
        x = hf_repr
        if self.use_relation_in_router and rel_feat is not None:
            x = torch.cat([x, rel_feat], dim=-1)
        return x

    def forward(self, x, x1=None):
        x = torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

        # low
        x_lf_seq_all = x[:, :, :self.n_lf]
        x_lf_seq = x_lf_seq_all[:, :, :self.use_lf_dim]

        # high
        x_hf = x[:, :, self.n_lf:]

        # encode high
        hf_out = self.hf_mlps(x_hf)
        hf_out = hf_out[:, -1, :]
        hf_repr = self.hf_decode(hf_out)

        # encode low dynamic
        dynamic_lf = self._build_dynamic_lf_input(x_lf_seq)
        lf_repr = self.lf_encoder(dynamic_lf)

        # relation summary
        raw_relation, rel_feat = self._build_relation_summary(hf_repr, lf_repr)

        # base HF prediction
        y_hf = self.expert_hf(hf_repr)

        # grouped FiLM + grouped LF residual
        lf_mod, group_w, gamma_all, beta_all = self.grouped_film(
            hf_repr=hf_repr,
            lf_repr=lf_repr,
            film_scale=self.film_scale,
        )

        # optional relation refine for group weight
        if self.group_router_refine is not None:
            refine_in = torch.cat([group_w, rel_feat], dim=-1)
            refine_logits = self.group_router_refine(refine_in)
            group_w = torch.softmax(refine_logits, dim=-1)

        group_lf_preds = []
        for k in range(self.num_film_groups):
            group_lf_pred = self.group_expert_lf[k](lf_mod)
            group_lf_preds.append(group_lf_pred)

        group_lf_preds = torch.stack(group_lf_preds, dim=1)  # [B, K, nopt]
        d_lf = (group_lf_preds * group_w.unsqueeze(-1)).sum(dim=1)

        # interaction correction
        expert_x_in = self._build_expert_x_input(hf_repr, lf_repr, rel_feat)
        d_x = self.expert_x(expert_x_in)

        # router
        router_in = self._build_router_input(hf_repr, rel_feat)
        gate_logits = self.router(router_in)
        a_lf = torch.sigmoid(gate_logits[:, 0:1])
        a_x = torch.sigmoid(gate_logits[:, 1:2])

        y = y_hf + a_lf * d_lf + a_x * d_x

        self._last_a_lf = a_lf
        self._last_a_x = a_x

        if self.training:
            current = x_lf_seq[:, -1, :]
            prev = x_lf_seq[:, -2, :] if x_lf_seq.size(1) >= 2 else torch.zeros_like(current)
            diff1 = current - prev
            upd_mask = (torch.abs(diff1) > self.mask_threshold).float()
            age_feat = self._compute_age_feature(x_lf_seq)

            stats = {
                "a_lf_mean": a_lf.mean().item(),
                "a_x_mean": a_x.mean().item(),
                "a_lf_std": a_lf.std().item(),
                "a_x_std": a_x.std().item(),
                "a_lf_min": a_lf.min().item(),
                "a_lf_max": a_lf.max().item(),
                "a_x_min": a_x.min().item(),
                "a_x_max": a_x.max().item(),

                "hf_repr_abs_mean": hf_repr.abs().mean().item(),
                "lf_repr_abs_mean": lf_repr.abs().mean().item(),
                "lf_mod_abs_mean": lf_mod.abs().mean().item(),

                "lf_current_abs_mean": current.abs().mean().item(),
                "lf_diff1_abs_mean": diff1.abs().mean().item(),
                "lf_upd_mask_mean": upd_mask.mean().item(),
                "lf_age_mean": age_feat.mean().item(),

                "rel_cos_mean": raw_relation[:, 0].mean().item(),
                "rel_norm_gap_mean": raw_relation[:, 1].mean().item(),
                "rel_dot_scaled_mean": raw_relation[:, 2].mean().item(),
                "rel_abs_diff_mean": raw_relation[:, 3].mean().item(),
                "rel_feat_abs_mean": rel_feat.abs().mean().item(),

                "group_entropy": (
                    -(group_w * torch.log(group_w.clamp_min(1e-12))).sum(dim=-1).mean().item()
                ),
            }

            for k in range(self.num_film_groups):
                stats[f"group_w_{k}_mean"] = group_w[:, k].mean().item()
                stats[f"gamma_abs_mean_{k}"] = gamma_all[:, k, :].abs().mean().item()
                stats[f"beta_abs_mean_{k}"] = beta_all[:, k, :].abs().mean().item()
                stats[f"group_lf_pred_abs_mean_{k}"] = group_lf_preds[:, k, :].abs().mean().item()

            self._last_stats = stats

        return y

    def get_router_loss(self):
        return next(self.parameters()).new_tensor(0.0)

    def get_expert_stats(self):
        return self._last_stats if hasattr(self, "_last_stats") else {}
