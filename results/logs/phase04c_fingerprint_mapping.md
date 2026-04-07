# Phase 04c Forward Differential Fingerprint Mapping

## Baseline

- Good reference: `good-21`
- Experimental defect sample: `bad-20-2`
- Fixed theoretical air gap: `40.0 nm`
- good-21 6p chi-square: `0.002564`
- good-21 baseline parameters: `d_bulk=444.423 nm`, `d_rough=51.188 nm`, `sigma=26.232 nm`, `ito_alpha=13.342829`, `pvk_b_scale=1.689435`, `niox_k=0.499533`

## Experimental Delta

- max(|Delta_R_exp|) = `10.135%`
- normalized range = `[-1.000, +0.279]`

## Theoretical Fingerprint Alignment

- L1 Glass/ITO: max(|Delta_R|) = `6.919%`, normalized RMSE = `1.156029`
- L2 ITO/NiOx: max(|Delta_R|) = `5.583%`, normalized RMSE = `0.611901`
- L3 SAM/PVK: max(|Delta_R|) = `9.134%`, normalized RMSE = `0.254985`

## Conclusion

- Best phase alignment: `L3 SAM/PVK`
- Interpretation: Phase 04c uses zero-preserving normalization to remove area-fraction amplitude ambiguity and compares only fingerprint morphology.
