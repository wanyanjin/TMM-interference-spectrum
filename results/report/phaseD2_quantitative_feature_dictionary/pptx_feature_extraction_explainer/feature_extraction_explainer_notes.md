# Feature Extraction Explainer Notes

## Slide 1 — Phase D-2 Feature Extraction Pipeline

- This is the core slide for the talk: one measured spectrum is not used directly for final fitting, but first converted into a routing-friendly feature layer.
- The five branches are complementary rather than redundant: windowed energy asks where the change lives, rear shift asks whether it behaves like thickness, rear spectral features ask whether the rear window becomes more complex, wavelet features localize reconstruction, and template similarity compares the full signature against family means.
- The `38 quantitative features` box is the compression step from full curves to interpretable numbers.
- The three right-hand boxes make the downstream role explicit: visualization, automatic routing, and then family-specific full-spectrum fitting.

## Slide 2 — Phase D-2 Feature Groups Overview

- This page is for explaining what each feature family is meant to answer.
- Windowed energy is the most direct spatial summary in wavelength space; rear-window shift is the most thickness-like descriptor; rear-window spectral features are for non-rigid rear reconstruction.
- Wavelet features emphasize localized structure and complexity, while template similarity gives a global family-level resemblance score.
- The summary route box is the key conclusion: five groups feed one compact routing layer, and that layer supports embedding, routing, and constrained fitting.

## Slide 3 — Why Not Use Raw Spectra Directly?

- The left side shows why directly classifying raw spectra is hard: the signal is high-dimensional, noise-sensitive, and difficult to interpret physically.
- The right side shows the proposed workflow: organize the spectrum into five feature groups, compress to 38 features, and then route before full-spectrum fitting.
- The bottom banner is the message to emphasize verbally: feature extraction is not the final inversion target; it is the front-end routing layer.
- If time is short, this is the best slide to use for motivating the whole D-2 approach before returning to the pipeline page.
