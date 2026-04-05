## 【参数数据表（含出处）】

**文中“CsFAPI”即 \(Cs_{0.1}FA_{0.9}PbI_3\)。作者在表中将三振子的中心能量记为 \(E_1,E_2,E_3\)（即各振子的 \(E_n/E_0\)）。**

| Sample | \(\varepsilon_\infty\) | \(E_g\) (eV) | \(A_1\) | \(E_1\) (eV) | \(C_1\) | \(A_2\) | \(E_2\) (eV) | \(C_2\) | \(A_3\) | \(E_3\) (eV) | \(C_3\) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Glass/CsFAPI | 1.10 | 1.59 | 24.53 | 1.57 | 0.13 | 7.60 | 2.46 | 0.49 | 6.50 | 3.31 | 3.89 |
| ITO/CsFAPI | 1.01 | 1.58 | 6.16 | 1.58 | 0.13 | 6.52 | 2.45 | 0.54 | 8.26 | 3.18 | 0.61 |

出处：**补充材料第 2 页**，**Table S1**（\(\varepsilon_\infty, A_1\sim C_3\)）与同页 **Table S2**（\(E_g\)）。  
引用：fileciteturn0file1

---

## 【数学模型公式（含出处）】

**注：正文将虚部/实部分别写作 \(\varepsilon_i,\varepsilon_r\)；下面等价写成 \(\varepsilon_2,\varepsilon_1\)。表中的 \(\varepsilon_\infty\) 对应正文里的 \(\varepsilon_r(\infty)\)。**

### 1) Tauc-Lorentz 虚部 \(\varepsilon_2(E)\)

$$
\varepsilon_2(E)=
\begin{cases}
\dfrac{A E_0 C (E-E_g)^2}{E\left[(E^2-E_0^2)^2+C^2E^2\right]}, & E>E_g,\\[8pt]
0, & E\le E_g.
\end{cases}
$$

### 2) Tauc-Lorentz 实部 \(\varepsilon_1(E)\)

$$
\varepsilon_1(E)=\varepsilon_r(\infty)
+\frac{A C\, a_{\ln}}{2\pi \xi^4 \alpha E_0}
\ln\!\left(\frac{E_0^2+E_g^2+\alpha E_g}{E_0^2+E_g^2-\alpha E_g}\right)
-\frac{A a_{\tan}}{\pi \xi^4 E_0}
\left[
\pi-\tan^{-1}\!\left(\frac{2E_g+\alpha}{C}\right)
+\tan^{-1}\!\left(\frac{\alpha-2E_g}{C}\right)
\right]
$$

$$
\quad
+\frac{2AE_0E_g(E^2-\gamma^2)}{\pi \xi^4 \alpha C}
\left[
\pi+2\tan^{-1}\!\left(\frac{2(\gamma^2-E_g^2)}{\alpha C}\right)
\right]
-\frac{AE_0C(E^2+E_g^2)}{\pi \xi^4 E}
\ln\!\left|\frac{E-E_g}{E+E_g}\right|
+\frac{2AE_0CE_g}{\pi \xi^4}
\ln\!\left(
\frac{|E-E_g|(E+E_g)}
{\sqrt{(E_0^2-E_g^2)^2+E_g^2C^2}}
\right).
$$

### 3) 文中同时定义的辅助量

$$
a_{\ln}=(E_g^2-E_0^2)E^2+E_g^2C^2-E_0^2(E_0^2+3E_g^2)
$$

$$
a_{\tan}=(E^2-E_0^2)(E_0^2+E_g^2)+E_g^2C^2
$$

$$
\xi^4=(E^2-\gamma^2)^2+\frac{\alpha^2C^2}{4},
\qquad
\alpha=\sqrt{4E_0^2-C^2},
\qquad
\gamma=\sqrt{E_0^2-\frac{C^2}{2}}.
$$

出处：**正文第 2513–2514 页**，T–L model 公式段落，即 “**The expression for \(\varepsilon_i\) in the Tauc-Lorentz model is...**” 和 “**The real part of the dielectric function, \(\varepsilon_r\), in the T–L model is given by...**” 后续公式与符号定义。该文在这里**直接给出了 \(\varepsilon_1\) 的闭式表达**，而不是单独再写一遍 Kramers-Kronig 积分式。  
引用：fileciteturn0file0
