# -*- coding: utf-8 -*-
"""工作3:工作2主干 + 工作1式低换手修正框架。已去掉 industry / pool 相关部分。

输入布局(featureCols 之后):
    x[:, :, 0:1298]    = 低换手 alpha1298
    x[:, :, 1298:1678] = 高换手 HF380(行业软中性化 soft_HF,λ=0.8)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from model_work2_backbone import DecisionAwareGraphAwareHF


class DynamicLowFreqEncoder(nn.Module):
    """低换手因子动态编码:当前值 / 一阶差分 / 更新掩码 / 陈旧度 age / 窗口均值。"""

    def __init__(self, lf_dim, out_dim, hidden_dim=512, p=0.0, skip_last_lf=9, diff_scale=1.0, mask_threshold=1e-8):
        super().__init__()
        self.lf_dim = int(lf_dim)
        self.out_dim = int(out_dim)
        self.hidden_dim = int(hidden_dim)
        self.skip_last_lf = int(skip_last_lf)
        self.diff_scale = float(diff_scale)
        self.mask_threshold = float(mask_threshold)
        self.base_lf_dim = self.lf_dim - self.skip_last_lf
        if self.base_lf_dim <= 0:
            raise ValueError(f"lf_dim - skip_last_lf must be positive, got {self.lf_dim} - {self.skip_last_lf}")
        self.dynamic_dim = self.base_lf_dim * 5
        self.net = nn.Sequential(
            nn.LayerNorm(self.dynamic_dim),
            nn.Linear(self.dynamic_dim, self.hidden_dim),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(self.hidden_dim, self.out_dim),
            nn.GELU(),
            nn.Dropout(float(p)),
        )
        self._last_stats = {}

    def _compute_age_feature(self, x):
        b, t, d = x.shape
        if t <= 1:
            return x.new_zeros(b, d)
        diffs = torch.abs(x[:, 1:, :] - x[:, :-1, :])
        changed = (diffs > self.mask_threshold).float()
        changed_rev = torch.flip(changed, dims=[1])
        idx = torch.arange(t - 1, device=x.device, dtype=x.dtype).view(1, t - 1, 1)
        big = x.new_full((b, t - 1, d), float(t - 1))
        dist = torch.where(changed_rev > 0, idx.expand_as(changed_rev), big)
        min_dist = dist.min(dim=1).values
        return min_dist / max(t - 1, 1)

    def forward(self, lf_x):
        lf_x = torch.nan_to_num(lf_x, nan=0.0, posinf=0.0, neginf=0.0)
        lf_x = lf_x[:, :, :self.base_lf_dim]
        current = lf_x[:, -1, :]
        if lf_x.size(1) >= 2:
            prev = lf_x[:, -2, :]
        else:
            prev = torch.zeros_like(current)
        diff_raw = current - prev
        diff = self.diff_scale * diff_raw
        update_mask = (torch.abs(diff_raw) > self.mask_threshold).float()
        age = self._compute_age_feature(lf_x)
        mean = lf_x.mean(dim=1)
        feat = torch.cat([current, diff, update_mask, age, mean], dim=-1)
        out = self.net(feat)
        if self.training:
            with torch.no_grad():
                self._last_stats = {
                    "lf_current_abs_mean": current.abs().mean().item(),
                    "lf_diff_abs_mean": diff_raw.abs().mean().item(),
                    "lf_update_mask_mean": update_mask.mean().item(),
                    "lf_age_mean": age.mean().item(),
                    "lf_mean_abs_mean": mean.abs().mean().item(),
                    "lf_repr_abs_mean": out.abs().mean().item(),
                }
        return out

    def get_stats(self):
        return self._last_stats if hasattr(self, "_last_stats") else {}


class LowFreqDualCorrectionHead(nn.Module):
    """低换手双专家修正头:LF 专家 + 交互专家 + sigmoid 路由,主干侧输入 detach。"""

    def __init__(
        self,
        repr_dim,
        nopt=1,
        relation_hidden=64,
        expert_hidden=256,
        router_hidden=128,
        p=0.0,
        fusion_scale_init=0.03,
        router_bias_init=-1.5,
        expert_init_std=0.01,
        detach_hf=True,
        detach_y=True,
        use_lf_expert=True,
        use_interaction_expert=True,
    ):
        super().__init__()
        self.repr_dim = int(repr_dim)
        self.nopt = int(nopt)
        self.relation_hidden = int(relation_hidden)
        self.detach_hf = bool(detach_hf)
        self.detach_y = bool(detach_y)
        self.use_lf_expert = bool(use_lf_expert)
        self.use_interaction_expert = bool(use_interaction_expert)
        raw_relation_dim = 4 + self.nopt * 2
        self.relation_proj = nn.Sequential(
            nn.LayerNorm(raw_relation_dim),
            nn.Linear(raw_relation_dim, self.relation_hidden),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(self.relation_hidden, self.relation_hidden),
            nn.GELU(),
        )
        self.lf_expert = nn.Sequential(
            nn.LayerNorm(self.repr_dim + self.relation_hidden),
            nn.Linear(self.repr_dim + self.relation_hidden, int(expert_hidden)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(expert_hidden), self.nopt),
        )
        interaction_dim = self.repr_dim * 4 + self.relation_hidden + self.nopt * 2
        self.interaction_expert = nn.Sequential(
            nn.LayerNorm(interaction_dim),
            nn.Linear(interaction_dim, int(expert_hidden)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(expert_hidden), int(expert_hidden)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(expert_hidden), self.nopt),
        )
        router_dim = self.repr_dim * 2 + self.relation_hidden + self.nopt * 2
        self.router = nn.Sequential(
            nn.LayerNorm(router_dim),
            nn.Linear(router_dim, int(router_hidden)),
            nn.GELU(),
            nn.Dropout(float(p)),
            nn.Linear(int(router_hidden), 2),
        )
        nn.init.normal_(self.lf_expert[-1].weight, std=float(expert_init_std))
        nn.init.constant_(self.lf_expert[-1].bias, 0.0)
        nn.init.normal_(self.interaction_expert[-1].weight, std=float(expert_init_std))
        nn.init.constant_(self.interaction_expert[-1].bias, 0.0)
        nn.init.normal_(self.router[-1].weight, std=0.01)
        nn.init.constant_(self.router[-1].bias, float(router_bias_init))
        self.fusion_scale = nn.Parameter(torch.tensor(float(fusion_scale_init)))
        self._last_stats = {}

    def _build_relation(self, hf_repr, lf_repr, y_hf):
        eps = 1e-8
        cos_sim = F.cosine_similarity(hf_repr, lf_repr, dim=-1, eps=eps).unsqueeze(-1)
        norm_gap = torch.norm(hf_repr - lf_repr, dim=-1, keepdim=True)
        dot_scaled = (hf_repr * lf_repr).sum(dim=-1, keepdim=True) / math.sqrt(float(hf_repr.size(-1)))
        abs_diff_mean = torch.mean(torch.abs(hf_repr - lf_repr), dim=-1, keepdim=True)
        raw_relation = torch.cat([cos_sim, norm_gap, dot_scaled, abs_diff_mean, y_hf, torch.abs(y_hf)], dim=-1)
        rel_feat = self.relation_proj(raw_relation)
        return raw_relation, rel_feat

    def forward(self, hf_repr, lf_repr, y_hf):
        hf_ctx = hf_repr.detach() if self.detach_hf else hf_repr
        y_ctx = y_hf.detach() if self.detach_y else y_hf
        raw_relation, rel_feat = self._build_relation(hf_ctx, lf_repr, y_ctx)
        d_lf = self.lf_expert(torch.cat([lf_repr, rel_feat], dim=-1))
        d_x = self.interaction_expert(torch.cat([hf_ctx, lf_repr, hf_ctx * lf_repr, hf_ctx - lf_repr, rel_feat, y_ctx, torch.abs(y_ctx)], dim=-1))
        gate = torch.sigmoid(self.router(torch.cat([hf_ctx, lf_repr, rel_feat, y_ctx, torch.abs(y_ctx)], dim=-1)))
        a_lf = gate[:, 0:1]
        a_x = gate[:, 1:2]
        if not self.use_lf_expert:
            d_lf = torch.zeros_like(d_lf)
            a_lf = torch.zeros_like(a_lf)
        if not self.use_interaction_expert:
            d_x = torch.zeros_like(d_x)
            a_x = torch.zeros_like(a_x)
        correction = self.fusion_scale * (a_lf * d_lf + a_x * d_x)
        if self.training:
            with torch.no_grad():
                self._last_stats = {
                    "a_lf_mean": a_lf.mean().item(),
                    "a_lf_std": a_lf.std(unbiased=False).item(),
                    "a_lf_min": a_lf.min().item(),
                    "a_lf_max": a_lf.max().item(),
                    "a_x_mean": a_x.mean().item(),
                    "a_x_std": a_x.std(unbiased=False).item(),
                    "a_x_min": a_x.min().item(),
                    "a_x_max": a_x.max().item(),
                    "d_lf_abs_mean": d_lf.abs().mean().item(),
                    "d_x_abs_mean": d_x.abs().mean().item(),
                    "correction_abs_mean": correction.abs().mean().item(),
                    "fusion_scale": self.fusion_scale.detach().item(),
                    "rel_cos_mean": raw_relation[:, 0].mean().item(),
                    "rel_norm_gap_mean": raw_relation[:, 1].mean().item(),
                    "rel_dot_scaled_mean": raw_relation[:, 2].mean().item(),
                    "rel_abs_diff_mean": raw_relation[:, 3].mean().item(),
                }
        return correction

    def get_stats(self):
        return self._last_stats if hasattr(self, "_last_stats") else {}


class HighTurnoverWithLowFreqMoE(nn.Module):
    """工作3 模型:图感知高换手主干 + 低换手动态修正(detach 解耦训练)。"""

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
        lf_dim=1298,
        hf_start=1298,
        hf_dim=380,
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
        lf_hidden=512,
        relation_hidden=64,
        expert_hidden=256,
        router_hidden=128,
        skip_last_lf=9,
        diff_scale=1.0,
        mask_threshold=1e-8,
        fusion_scale_init=0.03,
        router_bias_init=-1.5,
        expert_init_std=0.01,
        detach_hf=True,
        detach_y=True,
        use_lf_expert=True,
        use_interaction_expert=True,
    ):
        super().__init__()
        self.ninp = int(ninp)
        self.hf_start = int(hf_start)
        self.hf_dim = int(hf_dim)
        self.lf_dim = int(lf_dim)
        self.nopt = int(nopt)
        if self.hf_start < 0:
            raise ValueError(f"hf_start must be >= 0, got {self.hf_start}")
        if self.hf_dim <= 0:
            raise ValueError(f"hf_dim must be positive, got {self.hf_dim}")
        self.hf_end = self.hf_start + self.hf_dim
        if self.hf_end > self.ninp:
            raise ValueError(f"hf_start + hf_dim = {self.hf_end} > ninp = {self.ninp}")
        if self.lf_dim <= 0 or self.lf_dim > self.ninp:
            raise ValueError(f"invalid lf_dim={self.lf_dim}, ninp={self.ninp}")
        self.hf_backbone = DecisionAwareGraphAwareHF(
            ninp=self.hf_dim,
            nhead=nhead,
            nhid=nhid,
            nlayers=nlayers,
            p=p,
            slen=slen,
            nopt=nopt,
            nfc=nfc,
            token_dim=token_dim,
            factor_token_hidden=factor_token_hidden,
            cmix_layers=cmix_layers,
            ffn_mult=ffn_mult,
            head_hidden=head_hidden,
            factor_drop=factor_drop,
            use_factor_id=use_factor_id,
            use_linear_attention=use_linear_attention,
            use_checkpoint=use_checkpoint,
            batch_chunk_size=batch_chunk_size,
            graph_hidden=graph_hidden,
            graph_scale=graph_scale,
            use_graph_gate=use_graph_gate,
            graph_context_dim=graph_context_dim,
            tmix_init_scale=tmix_init_scale,
            cmix_init_scale=cmix_init_scale,
            head_pool=head_pool,
            use_delta_head=use_delta_head,
            delta_hidden=delta_hidden,
            delta_scale_init=delta_scale_init,
            delta_type=delta_type,
            use_decision_aux=use_decision_aux,
            decision_hidden=decision_hidden,
            aux_head_hidden=aux_head_hidden,
            aux_init_scale=aux_init_scale,
            decision_mode=decision_mode,
            use_amp_gate=use_amp_gate,
            amp_hidden=amp_hidden,
            amp_scale_init=amp_scale_init,
            input_factor_drop=input_factor_drop,
        )
        if str(head_pool) == "last":
            repr_dim = self.hf_dim
        elif str(head_pool) == "last_mean":
            repr_dim = self.hf_dim * 2
        elif str(head_pool) == "last_mean_std":
            repr_dim = self.hf_dim * 3
        else:
            raise ValueError("head_pool must be one of: last, last_mean, last_mean_std")
        self.lf_encoder = DynamicLowFreqEncoder(self.lf_dim, repr_dim, lf_hidden, p, skip_last_lf, diff_scale, mask_threshold)
        self.lf_correction = LowFreqDualCorrectionHead(
            repr_dim=repr_dim,
            nopt=nopt,
            relation_hidden=relation_hidden,
            expert_hidden=expert_hidden,
            router_hidden=router_hidden,
            p=p,
            fusion_scale_init=fusion_scale_init,
            router_bias_init=router_bias_init,
            expert_init_std=expert_init_std,
            detach_hf=detach_hf,
            detach_y=detach_y,
            use_lf_expert=use_lf_expert,
            use_interaction_expert=use_interaction_expert,
        )
        self._last_stats = {}

    def _split_lf_hf(self, x):
        lf_x = x[:, :, :self.lf_dim]
        hf_x = x[:, :, self.hf_start:self.hf_end]
        return lf_x, hf_x

    def forward(self, x, x1=None):
        x = torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        lf_x, hf_x = self._split_lf_hf(x)
        y_hf, hf_repr = self.hf_backbone(hf_x, return_repr=True)
        lf_repr = self.lf_encoder(lf_x)
        correction = self.lf_correction(hf_repr=hf_repr, lf_repr=lf_repr, y_hf=y_hf)
        y = y_hf + correction
        if y.dim() == 1:
            y = y.view(-1, 1)
        if self.training:
            stats = {}
            if hasattr(self.hf_backbone, "get_expert_stats"):
                stats.update({f"hf_{k}": v for k, v in self.hf_backbone.get_expert_stats().items()})
            stats.update({f"lfenc_{k}": v for k, v in self.lf_encoder.get_stats().items()})
            stats.update({f"lfcorr_{k}": v for k, v in self.lf_correction.get_stats().items()})
            with torch.no_grad():
                stats.update({
                    "y_hf_abs_mean": y_hf.abs().mean().item(),
                    "y_final_abs_mean": y.abs().mean().item(),
                    "correction_abs_mean": correction.abs().mean().item(),
                    "correction_over_hf": (correction.abs().mean() / y_hf.abs().mean().clamp_min(1e-6)).item(),
                })
            self._last_stats = stats
            return y
        if hasattr(self.hf_backbone, "get_expert_stats"):
            self._last_stats = {f"hf_{k}": v for k, v in self.hf_backbone.get_expert_stats().items()}
        else:
            self._last_stats = {}
        return y

    def get_router_loss(self):
        return next(self.parameters()).new_tensor(0.0)

    def get_expert_stats(self):
        return self._last_stats if hasattr(self, "_last_stats") else {}
