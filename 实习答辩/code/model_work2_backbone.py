# -*- coding: utf-8 -*-
"""工作2:纯高换手主干(图感知因子混合 + 决策感知输出端)。已去掉 industry / pool 相关封装。"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint


class MlpBlock(nn.Module):
    def __init__(self, input_dim, hidden_dim, p=0.0):
        super().__init__()
        input_dim = int(input_dim)
        hidden_dim = int(hidden_dim)
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(hidden_dim, input_dim),
            nn.Dropout(float(p)),
        )

    def forward(self, x):
        return self.net(x)


class MLPTmix(nn.Module):
    def __init__(self, seq_len, feature_dim, temporal_hidden_dim=64, p=0.0, init_scale=1.0):
        super().__init__()
        self.seq_len = int(seq_len)
        self.feature_dim = int(feature_dim)
        self.norm = nn.LayerNorm(self.feature_dim)
        self.temporal_mlp = MlpBlock(self.seq_len, int(temporal_hidden_dim), p)
        self.out_scale = nn.Parameter(torch.tensor(float(init_scale)))

    def forward(self, x):
        h = self.norm(x)
        h = h.permute(0, 2, 1).contiguous()
        h = self.temporal_mlp(h)
        h = h.permute(0, 2, 1).contiguous()
        return self.out_scale * h


class LinearFactorAttention(nn.Module):
    def __init__(self, token_dim, num_heads=1, p=0.0):
        super().__init__()
        self.token_dim = int(token_dim)
        self.num_heads = int(num_heads)
        if self.token_dim % self.num_heads != 0:
            raise ValueError(f"token_dim={self.token_dim} must be divisible by num_heads={self.num_heads}")
        self.head_dim = self.token_dim // self.num_heads
        self.q_proj = nn.Linear(self.token_dim, self.token_dim)
        self.k_proj = nn.Linear(self.token_dim, self.token_dim)
        self.v_proj = nn.Linear(self.token_dim, self.token_dim)
        self.out_proj = nn.Linear(self.token_dim, self.token_dim)
        self.drop = nn.Dropout(float(p))

    @staticmethod
    def feature_map(x):
        return F.elu(x) + 1.0

    def forward(self, x):
        b, c, d = x.shape
        h = self.num_heads
        dh = self.head_dim
        q = self.q_proj(x).view(b, c, h, dh).transpose(1, 2)
        k = self.k_proj(x).view(b, c, h, dh).transpose(1, 2)
        v = self.v_proj(x).view(b, c, h, dh).transpose(1, 2)
        q = self.feature_map(q)
        k = self.feature_map(k)
        v = self.drop(v)
        kv = torch.einsum("bhnd,bhne->bhde", k, v)
        k_sum = k.sum(dim=2)
        z = 1.0 / torch.einsum("bhnd,bhd->bhn", q, k_sum).clamp_min(1e-6)
        out = torch.einsum("bhnd,bhde,bhn->bhne", q, kv, z)
        out = out.transpose(1, 2).contiguous().view(b, c, d)
        return self.out_proj(out)


class GraphAwareFactorEncoderBlock(nn.Module):
    def __init__(self, token_dim, num_heads=1, ffn_mult=2, p=0.0, use_linear_attention=True):
        super().__init__()
        token_dim = int(token_dim)
        self.use_linear_attention = bool(use_linear_attention)
        self.norm1 = nn.LayerNorm(token_dim)
        if self.use_linear_attention:
            self.attn = LinearFactorAttention(token_dim, int(num_heads), p)
        else:
            self.attn = nn.MultiheadAttention(token_dim, int(num_heads), dropout=float(p), batch_first=True)
        self.norm2 = nn.LayerNorm(token_dim)
        self.ffn = nn.Sequential(
            nn.Linear(token_dim, token_dim * int(ffn_mult)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(token_dim * int(ffn_mult), token_dim),
            nn.Dropout(float(p)),
        )

    def forward(self, tokens):
        h = self.norm1(tokens)
        if self.use_linear_attention:
            tokens = tokens + self.attn(h)
        else:
            attn_out, _ = self.attn(h, h, h, need_weights=False)
            tokens = tokens + attn_out
        tokens = tokens + self.ffn(self.norm2(tokens))
        return tokens


class GraphAwareCmix(nn.Module):
    def __init__(
        self,
        seq_len,
        feature_dim,
        token_dim=16,
        factor_token_hidden=128,
        num_heads=1,
        cmix_layers=1,
        ffn_mult=2,
        p=0.0,
        factor_drop=0.05,
        use_factor_id=True,
        use_linear_attention=True,
        graph_hidden=64,
        graph_scale=0.05,
        use_graph_gate=True,
        graph_context_dim=0,
        init_scale=0.03,
    ):
        super().__init__()
        self.seq_len = int(seq_len)
        self.feature_dim = int(feature_dim)
        self.token_dim = int(token_dim)
        self.factor_token_hidden = int(factor_token_hidden) if factor_token_hidden is not None else 128
        self.factor_drop = float(factor_drop)
        self.use_graph_gate = bool(use_graph_gate)
        self.graph_context_dim = int(graph_context_dim)
        self.norm_t = nn.LayerNorm(self.seq_len)
        self.token_proj = nn.Sequential(
            nn.Linear(self.seq_len, self.factor_token_hidden),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(self.factor_token_hidden, self.token_dim),
            nn.Dropout(float(p)),
        )
        if bool(use_factor_id):
            self.factor_emb = nn.Parameter(torch.randn(self.feature_dim, self.token_dim) * 0.02)
        else:
            self.factor_emb = None
        if self.use_graph_gate:
            graph_in_dim = 4 + self.graph_context_dim
            self.graph_node_gate = nn.Sequential(
                nn.LayerNorm(graph_in_dim),
                nn.Linear(graph_in_dim, int(graph_hidden)),
                nn.GELU(),
                nn.Dropout(float(p)),
                nn.Linear(int(graph_hidden), 1),
            )
            self.graph_token_bias = nn.Sequential(
                nn.LayerNorm(graph_in_dim),
                nn.Linear(graph_in_dim, int(graph_hidden)),
                nn.GELU(),
                nn.Dropout(float(p)),
                nn.Linear(int(graph_hidden), self.token_dim),
            )
            self.graph_scale = nn.Parameter(torch.tensor(float(graph_scale)))
        else:
            self.graph_node_gate = None
            self.graph_token_bias = None
            self.graph_scale = None
        self.encoder = nn.ModuleList([
            GraphAwareFactorEncoderBlock(self.token_dim, int(num_heads), int(ffn_mult), p, use_linear_attention)
            for _ in range(int(cmix_layers))
        ])
        self.out_proj = nn.Sequential(
            nn.LayerNorm(self.token_dim),
            nn.Linear(self.token_dim, self.factor_token_hidden),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(self.factor_token_hidden, self.seq_len),
        )
        self.out_gate = nn.Sequential(
            nn.LayerNorm(self.token_dim * 2),
            nn.Linear(self.token_dim * 2, self.token_dim),
            nn.GELU(),
            nn.Linear(self.token_dim, 1),
        )
        self.out_scale = nn.Parameter(torch.tensor(float(init_scale)))
        self._last_graph_stats = {}

    def _factor_dropout(self, tokens):
        if (not self.training) or self.factor_drop <= 0:
            return tokens
        keep_prob = 1.0 - self.factor_drop
        mask = torch.empty(tokens.size(0), tokens.size(1), 1, device=tokens.device, dtype=tokens.dtype).bernoulli_(keep_prob)
        return tokens * mask / max(keep_prob, 1e-6)

    @staticmethod
    def _build_graph_state(h):
        last = h[:, :, -1:].contiguous()
        if h.size(-1) >= 2:
            diff = h[:, :, -1:] - h[:, :, -2:-1]
        else:
            diff = torch.zeros_like(last)
        return torch.cat([last, diff, torch.abs(last), torch.abs(diff)], dim=-1)

    def _apply_graph_gate(self, tokens, h, graph_context=None):
        if not self.use_graph_gate:
            return tokens
        b, c, _ = tokens.shape
        graph_state = self._build_graph_state(h)
        if self.graph_context_dim > 0:
            if graph_context is None:
                ctx = tokens.new_zeros(b, self.graph_context_dim)
            else:
                if graph_context.dim() != 2 or graph_context.size(0) != b or graph_context.size(1) != self.graph_context_dim:
                    raise ValueError(f"graph_context must be [B, {self.graph_context_dim}], got shape={tuple(graph_context.shape)}")
                ctx = graph_context
            ctx = ctx.unsqueeze(1).expand(b, c, self.graph_context_dim)
            graph_state = torch.cat([graph_state, ctx], dim=-1)
        node_gate = torch.tanh(self.graph_node_gate(graph_state))
        token_bias = torch.tanh(self.graph_token_bias(graph_state))
        scale = self.graph_scale
        tokens = tokens * (1.0 + scale * node_gate) + scale * token_bias
        if self.training:
            with torch.no_grad():
                self._last_graph_stats = {
                    "graph_gate_mean": node_gate.mean().item(),
                    "graph_gate_std": node_gate.std(unbiased=False).item(),
                    "graph_gate_abs_mean": node_gate.abs().mean().item(),
                    "graph_token_bias_abs_mean": token_bias.abs().mean().item(),
                    "graph_scale": scale.detach().item(),
                }
        return tokens

    def forward(self, x, graph_context=None):
        h = x.permute(0, 2, 1).contiguous()
        h = self.norm_t(h)
        tokens = self.token_proj(h)
        if self.factor_emb is not None:
            tokens = tokens + self.factor_emb.unsqueeze(0).to(device=tokens.device, dtype=tokens.dtype)
        tokens = self._apply_graph_gate(tokens, h, graph_context)
        tokens = self._factor_dropout(tokens)
        for block in self.encoder:
            tokens = block(tokens)
        token_mean = tokens.mean(dim=1)
        token_std = tokens.std(dim=1, unbiased=False)
        gate = torch.sigmoid(self.out_gate(torch.cat([token_mean, token_std], dim=-1)))
        out = self.out_proj(tokens)
        out = out.permute(0, 2, 1).contiguous()
        return self.out_scale * gate.view(-1, 1, 1) * out

    def get_graph_stats(self):
        return self._last_graph_stats if hasattr(self, "_last_graph_stats") else {}


class DecisionAwareGraphBlock(nn.Module):
    def __init__(
        self,
        seq_len,
        feature_dim,
        temporal_hidden_dim=64,
        token_dim=16,
        factor_token_hidden=128,
        num_heads=1,
        cmix_layers=1,
        ffn_mult=2,
        p=0.0,
        factor_drop=0.05,
        use_factor_id=True,
        use_linear_attention=True,
        graph_hidden=64,
        graph_scale=0.05,
        use_graph_gate=True,
        graph_context_dim=0,
        tmix_init_scale=1.0,
        cmix_init_scale=0.03,
        use_checkpoint=False,
    ):
        super().__init__()
        self.use_checkpoint = bool(use_checkpoint)
        self.tmix = MLPTmix(seq_len, feature_dim, temporal_hidden_dim, p, tmix_init_scale)
        self.cmix = GraphAwareCmix(
            seq_len,
            feature_dim,
            token_dim,
            factor_token_hidden,
            num_heads,
            cmix_layers,
            ffn_mult,
            p,
            factor_drop,
            use_factor_id,
            use_linear_attention,
            graph_hidden,
            graph_scale,
            use_graph_gate,
            graph_context_dim,
            cmix_init_scale,
        )

    @staticmethod
    def _rms(x, eps=1e-6):
        return torch.sqrt(torch.mean(x * x, dim=(1, 2)) + eps)

    @staticmethod
    def _mean_abs(x):
        return torch.mean(torch.abs(x), dim=(1, 2))

    def _forward_impl(self, x, graph_context=None):
        u_t = self.tmix(x)
        x_t = x + u_t
        u_c = self.cmix(x_t, graph_context=graph_context)
        x_o = x_t + u_c
        eps = 1e-6
        x_rms = self._rms(x).clamp_min(eps)
        ut_rms = self._rms(u_t)
        uc_rms = self._rms(u_c)
        stats = torch.stack([
            ut_rms / x_rms,
            uc_rms / x_rms,
            uc_rms / ut_rms.clamp_min(eps),
            self._mean_abs(u_t),
            self._mean_abs(u_c),
            self._mean_abs(u_c - u_t),
        ], dim=-1)
        return x_o, stats

    def forward(self, x, graph_context=None):
        if self.use_checkpoint and self.training and x.requires_grad:
            if graph_context is None:
                return checkpoint(self._forward_impl, x, use_reentrant=False)
            def custom_forward(inp, ctx):
                return self._forward_impl(inp, graph_context=ctx)
            return checkpoint(custom_forward, x, graph_context, use_reentrant=False)
        return self._forward_impl(x, graph_context=graph_context)

    def get_graph_stats(self):
        return self.cmix.get_graph_stats()


class DeltaHeadAdapter(nn.Module):
    def __init__(self, feature_dim, nopt=1, hidden_dim=128, p=0.0, init_scale=0.01, delta_type="last_diff"):
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.nopt = int(nopt)
        self.delta_type = str(delta_type)
        if self.delta_type not in ("last_diff", "last_prev"):
            raise ValueError("delta_type must be one of: last_diff, last_prev")
        in_dim = self.feature_dim * 3
        self.net = nn.Sequential(
            nn.LayerNorm(in_dim),
            nn.Linear(in_dim, int(hidden_dim)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(hidden_dim), self.nopt),
        )
        self.delta_scale = nn.Parameter(torch.tensor(float(init_scale)))
        self._last_delta_abs = None

    def forward(self, h):
        h_last = h[:, -1, :]
        if h.size(1) >= 2:
            h_prev = h[:, -2, :]
        else:
            h_prev = torch.zeros_like(h_last)
        diff = h_last - h_prev
        if self.delta_type == "last_diff":
            feat = torch.cat([h_last, diff, torch.abs(diff)], dim=-1)
        elif self.delta_type == "last_prev":
            feat = torch.cat([h_last, h_prev, diff], dim=-1)
        else:
            raise RuntimeError("invalid delta_type")
        delta = self.delta_scale * self.net(feat)
        if self.training:
            self._last_delta_abs = delta.detach().abs().mean()
        return delta


class DecisionAwareAuxHead(nn.Module):
    def __init__(
        self,
        feature_dim,
        nopt=1,
        head_hidden=128,
        decision_hidden=128,
        stats_dim=6,
        p=0.0,
        aux_init_scale=0.03,
        mode="residual",
    ):
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.nopt = int(nopt)
        self.stats_dim = int(stats_dim)
        self.mode = str(mode)
        repr_dim = self.feature_dim * 3
        decision_in_dim = repr_dim + self.stats_dim
        self.aux_head = nn.Sequential(
            nn.LayerNorm(repr_dim),
            nn.Linear(repr_dim, int(head_hidden)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(head_hidden), self.nopt),
        )
        self.decision_head = nn.Sequential(
            nn.LayerNorm(decision_in_dim),
            nn.Linear(decision_in_dim, int(decision_hidden)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(decision_hidden), 1),
        )
        nn.init.constant_(self.decision_head[-1].bias, -1.5)
        nn.init.normal_(self.decision_head[-1].weight, std=0.01)
        self.aux_scale = nn.Parameter(torch.tensor(float(aux_init_scale)))
        self._last_alpha = None
        self._last_aux_abs = None

    def forward(self, h, stats):
        h_last = h[:, -1, :]
        h_mean = h.mean(dim=1)
        h_std = h.std(dim=1, unbiased=False)
        repr_feat = torch.cat([h_last, h_mean, h_std], dim=-1)
        aux = self.aux_head(repr_feat)
        decision_in = torch.cat([repr_feat, stats], dim=-1)
        alpha = torch.sigmoid(self.decision_head(decision_in))
        self._last_alpha = alpha.detach()
        self._last_aux_abs = aux.detach().abs().mean()
        if self.mode == "residual":
            return alpha * self.aux_scale * aux
        if self.mode == "confidence":
            return alpha * self.aux_scale * torch.tanh(aux)
        raise ValueError("mode must be one of: residual, confidence")


class OutputAmplitudeGate(nn.Module):
    def __init__(self, feature_dim, hidden_dim=128, stats_dim=6, p=0.0, init_scale=0.1):
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.stats_dim = int(stats_dim)
        in_dim = self.feature_dim * 3 + self.stats_dim
        self.net = nn.Sequential(
            nn.LayerNorm(in_dim),
            nn.Linear(in_dim, int(hidden_dim)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(hidden_dim), 1),
        )
        self.amp_scale = nn.Parameter(torch.tensor(float(init_scale)))
        self._last_amp = None

    def forward(self, y, h, stats):
        h_last = h[:, -1, :]
        h_mean = h.mean(dim=1)
        h_std = h.std(dim=1, unbiased=False)
        feat = torch.cat([h_last, h_mean, h_std, stats], dim=-1)
        amp = torch.tanh(self.net(feat))
        self._last_amp = amp.detach()
        return y * (1.0 + self.amp_scale * amp)


class DecisionAwareGraphAwareHF(nn.Module):
    def __init__(
        self,
        ninp,
        nhead,
        nhid,
        nlayers,
        p,
        slen,
        nopt,
        nfc,
        token_dim=16,
        factor_token_hidden=None,
        cmix_layers=1,
        ffn_mult=2,
        head_hidden=128,
        factor_drop=0.05,
        use_factor_id=True,
        use_linear_attention=True,
        use_checkpoint=True,
        batch_chunk_size=512,
        graph_hidden=64,
        graph_scale=0.05,
        use_graph_gate=True,
        graph_context_dim=0,
        tmix_init_scale=1.0,
        cmix_init_scale=0.03,
        head_pool="last",
        use_delta_head=True,
        delta_hidden=128,
        delta_scale_init=0.01,
        delta_type="last_diff",
        use_decision_aux=True,
        decision_hidden=128,
        aux_head_hidden=128,
        aux_init_scale=0.03,
        decision_mode="residual",
        use_amp_gate=True,
        amp_hidden=128,
        amp_scale_init=0.1,
        input_factor_drop=0.0,
    ):
        super().__init__()
        self.ninp = int(ninp)
        self.slen = int(slen)
        self.nopt = int(nopt)
        self.batch_chunk_size = batch_chunk_size
        self.head_pool = str(head_pool)
        self.use_delta_head = bool(use_delta_head)
        self.use_decision_aux = bool(use_decision_aux)
        self.use_amp_gate = bool(use_amp_gate)
        self.decision_mode = str(decision_mode)
        self.graph_context_dim = int(graph_context_dim)
        self.input_factor_drop = float(input_factor_drop)
        if factor_token_hidden is None:
            factor_token_hidden = int(nfc)
        num_heads = max(1, int(nhead))
        self.blocks = nn.ModuleList([
            DecisionAwareGraphBlock(
                seq_len=int(slen),
                feature_dim=self.ninp,
                temporal_hidden_dim=int(nhid),
                token_dim=token_dim,
                factor_token_hidden=factor_token_hidden,
                num_heads=num_heads,
                cmix_layers=cmix_layers,
                ffn_mult=ffn_mult,
                p=p,
                factor_drop=factor_drop,
                use_factor_id=use_factor_id,
                use_linear_attention=use_linear_attention,
                graph_hidden=graph_hidden,
                graph_scale=graph_scale,
                use_graph_gate=use_graph_gate,
                graph_context_dim=graph_context_dim,
                tmix_init_scale=tmix_init_scale,
                cmix_init_scale=cmix_init_scale,
                use_checkpoint=use_checkpoint,
            )
            for _ in range(int(nlayers))
        ])
        self.final_norm = nn.LayerNorm(self.ninp)
        if self.head_pool == "last":
            head_in_dim = self.ninp
        elif self.head_pool == "last_mean":
            head_in_dim = self.ninp * 2
        elif self.head_pool == "last_mean_std":
            head_in_dim = self.ninp * 3
        else:
            raise ValueError("head_pool must be one of: last, last_mean, last_mean_std")
        self.main_head = nn.Sequential(
            nn.LayerNorm(head_in_dim),
            nn.Linear(head_in_dim, int(head_hidden)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(head_hidden), self.nopt),
        )
        if self.use_delta_head:
            self.delta_head = DeltaHeadAdapter(self.ninp, self.nopt, delta_hidden, p, delta_scale_init, delta_type)
        else:
            self.delta_head = None
        if self.use_decision_aux:
            self.decision_aux = DecisionAwareAuxHead(self.ninp, self.nopt, aux_head_hidden, decision_hidden, 6, p, aux_init_scale, decision_mode)
        else:
            self.decision_aux = None
        if self.use_amp_gate:
            self.amp_gate = OutputAmplitudeGate(self.ninp, amp_hidden, 6, p, amp_scale_init)
        else:
            self.amp_gate = None
        self._last_stats = {}

    def _input_factor_dropout(self, x):
        if (not self.training) or self.input_factor_drop <= 0:
            return x
        keep_prob = 1.0 - self.input_factor_drop
        mask = torch.empty(x.size(0), 1, x.size(2), device=x.device, dtype=x.dtype).bernoulli_(keep_prob)
        return x * mask / max(keep_prob, 1e-6)

    def _pool_main(self, h):
        h_last = h[:, -1, :]
        if self.head_pool == "last":
            return h_last
        h_mean = h.mean(dim=1)
        if self.head_pool == "last_mean":
            return torch.cat([h_last, h_mean], dim=-1)
        if self.head_pool == "last_mean_std":
            h_std = h.std(dim=1, unbiased=False)
            return torch.cat([h_last, h_mean, h_std], dim=-1)
        raise RuntimeError("invalid head_pool")

    def _forward_impl(self, x, graph_context=None, return_repr=False):
        h = self._input_factor_dropout(x)
        stats_list = []
        graph_stats = {}
        for i, block in enumerate(self.blocks):
            h, stats = block(h, graph_context=graph_context)
            stats_list.append(stats)
            if self.training:
                block_graph_stats = block.get_graph_stats()
                for key, value in block_graph_stats.items():
                    graph_stats[f"block{i}_{key}"] = value
        h = self.final_norm(h)
        main_repr = self._pool_main(h)
        y_main = self.main_head(main_repr)
        if len(stats_list) > 1:
            update_stats = torch.stack(stats_list, dim=1).mean(dim=1)
        else:
            update_stats = stats_list[0]
        y = y_main
        if self.delta_head is not None:
            delta = self.delta_head(h)
            y = y + delta
        else:
            delta = None
        if self.decision_aux is not None:
            aux_delta = self.decision_aux(h, update_stats)
            if self.decision_mode == "residual":
                y = y + aux_delta
            elif self.decision_mode == "confidence":
                y = y * (1.0 + aux_delta)
            else:
                raise ValueError("decision_mode must be residual or confidence")
        if self.amp_gate is not None:
            y = self.amp_gate(y, h, update_stats)
        if self.training:
            with torch.no_grad():
                stats_dict = {
                    "update_ut_over_x_mean": update_stats[:, 0].mean().item(),
                    "update_uc_over_x_mean": update_stats[:, 1].mean().item(),
                    "update_uc_over_ut_mean": update_stats[:, 2].mean().item(),
                    "update_ut_abs_mean": update_stats[:, 3].mean().item(),
                    "update_uc_abs_mean": update_stats[:, 4].mean().item(),
                    "update_uc_minus_ut_abs_mean": update_stats[:, 5].mean().item(),
                    "y_main_abs_mean": y_main.abs().mean().item(),
                    "y_abs_mean": y.abs().mean().item(),
                    "main_repr_abs_mean": main_repr.abs().mean().item(),
                }
                if delta is not None:
                    stats_dict["delta_abs_mean"] = delta.abs().mean().item()
                    stats_dict["delta_scale"] = self.delta_head.delta_scale.detach().item()
                if self.decision_aux is not None and self.decision_aux._last_alpha is not None:
                    alpha = self.decision_aux._last_alpha
                    stats_dict.update({
                        "decision_alpha_mean": alpha.mean().item(),
                        "decision_alpha_std": alpha.std(unbiased=False).item(),
                        "decision_alpha_min": alpha.min().item(),
                        "decision_alpha_max": alpha.max().item(),
                        "decision_aux_abs_mean": self.decision_aux._last_aux_abs.item() if self.decision_aux._last_aux_abs is not None else 0.0,
                        "decision_aux_scale": self.decision_aux.aux_scale.detach().item(),
                    })
                if self.amp_gate is not None and self.amp_gate._last_amp is not None:
                    amp = self.amp_gate._last_amp
                    stats_dict.update({
                        "amp_mean": amp.mean().item(),
                        "amp_std": amp.std(unbiased=False).item(),
                        "amp_min": amp.min().item(),
                        "amp_max": amp.max().item(),
                        "amp_scale": self.amp_gate.amp_scale.detach().item(),
                    })
                stats_dict.update(graph_stats)
                self._last_stats = stats_dict
        if return_repr:
            return y, main_repr
        return y

    def forward(self, x, x1=None, return_repr=False):
        x = torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        graph_context = None
        b = x.size(0)
        if self.batch_chunk_size is None or b <= self.batch_chunk_size:
            return self._forward_impl(x, graph_context=graph_context, return_repr=return_repr)
        if return_repr:
            outs = []
            reprs = []
            for st in range(0, b, self.batch_chunk_size):
                ed = min(st + self.batch_chunk_size, b)
                y_part, r_part = self._forward_impl(x[st:ed], graph_context=None, return_repr=True)
                outs.append(y_part)
                reprs.append(r_part)
            return torch.cat(outs, dim=0), torch.cat(reprs, dim=0)
        outs = []
        for st in range(0, b, self.batch_chunk_size):
            ed = min(st + self.batch_chunk_size, b)
            outs.append(self._forward_impl(x[st:ed], graph_context=None, return_repr=False))
        return torch.cat(outs, dim=0)

    def get_router_loss(self):
        return next(self.parameters()).new_tensor(0.0)

    def get_expert_stats(self):
        return self._last_stats if hasattr(self, "_last_stats") else {}
