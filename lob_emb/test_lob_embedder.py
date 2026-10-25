"""Smoke test: shapes, all-zero (missing) handling, no NaNs, gradient flow."""
import torch

from lob_embedder import LOBEmbedder, LOBConfig, RAW_DIM


def make_fake(B, T, S=10, missing_rows=0):
    raw = torch.zeros(B, T, S, RAW_DIM)
    mid = 10.0 + torch.rand(B, T, S) * 5
    raw[..., 0] = mid[..., :1]                        # open
    raw[..., 1] = mid                                 # mid
    raw[..., 2] = torch.cumsum(torch.rand(B, T, S) * 1e5, dim=-1)
    raw[..., 3] = 1e8                                 # float shares
    for off in (4, 204):
        sgn = 1.0 if off == 4 else -1.0
        lv = torch.arange(1, 21).float()
        raw[..., off:off + 20] = mid[..., None] * (1 + sgn * lv * 1e-4)   # p
        raw[..., off + 20:off + 40] = torch.randint(1, 50000, (B, T, S, 20)).float()  # v
        raw[..., off + 40:off + 60] = torch.randint(1, 200, (B, T, S, 20)).float()    # c
        raw[..., off + 60:off + 80] = torch.rand(B, T, S, 20)             # hhi
        raw[..., off + 80:off + 100] = torch.rand(B, T, S, 20) * 3600     # age
        raw[..., off + 100:off + 120] = torch.rand(B, T, S, 20)           # nr
        raw[..., off + 120:off + 140] = torch.randint(1, 5000, (B, T, S, 20)).float()  # hv
        raw[..., off + 140:off + 160] = torch.rand(B, T, S, 20) * 10      # wp
        raw[..., off + 160:off + 180] = torch.randint(0, 2000, (B, T, S, 20)).float()  # cv
        raw[..., off + 180:off + 200] = torch.randint(0, 60, (B, T, S, 20)).float()    # bt
    if missing_rows:
        raw[:, :missing_rows] = 0.0                   # early history: no LOB
    return raw


def main():
    torch.manual_seed(0)
    model = LOBEmbedder(LOBConfig())
    model.train()

    B, T = 4, 6
    raw = make_fake(B, T, missing_rows=3)

    emb, valid = model(raw)
    assert emb.shape == (B, T, 128), emb.shape
    assert valid.shape == (B, T)
    assert torch.isfinite(emb).all(), "NaN/Inf in embedding"
    assert (valid[:, :3] == 0).all() and (valid[:, 3:] == 1).all()

    # fully-missing tis map to the same learned null embedding (per eval mode)
    model.eval()
    with torch.no_grad():
        e2, _ = model(raw)
        null = e2[:, :3].reshape(-1, 128)
        assert (null - null[0]).abs().max() < 1e-5, "null emb should be constant"
    model.train()

    # gradient flow incl. aux loss
    emb, valid, aux = model.forward_with_aux(raw)
    loss = emb.square().mean() + 0.1 * aux
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.grad is not None]
    assert len(grads) > 0 and torch.stack([g.abs().sum() for g in grads]).sum() > 0
    assert all(torch.isfinite(g).all() for g in grads), \
        "NaN/Inf gradient (all-masked attention rows must stay safe)"
    assert torch.isfinite(aux), "aux loss not finite"

    # partial missing inside a ti (e.g. data glitch): still finite
    raw2 = make_fake(2, 2)
    raw2[0, 0, :4] = 0.0
    e3, v3 = model(raw2)
    assert torch.isfinite(e3).all()

    n_params = sum(p.numel() for p in model.parameters())
    print(f"OK. params={n_params/1e3:.0f}K, emb shape={tuple(emb.shape)}, "
          f"aux={aux.item():.4f}")


if __name__ == "__main__":
    main()
