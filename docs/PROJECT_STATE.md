# PROJECT_STATE.md

鏈枃浠剁敤浜庢寔缁悓姝?`TMM-interference-spectrum` 椤圭洰鐨勫綋鍓嶇姸鎬侊紝鏄悗缁?AI Agent 鍜屾灦鏋勫笀鎭㈠涓婁笅鏂囩殑棣栬鍏ュ彛銆?

## 1. Current Snapshot

- 更新时间：2026-05-07
- 当前判断 Phase：`Phase 09`
- 阶段定义：`建立工具平台架构规范、core 沙箱规则、输入 adapter 规则与 PySide6 + pyqtgraph GUI 技术路线，并新增最小 domain/storage/workflows/gui/common 骨架`
- 褰撳墠鍙敤鑳藉姏锛?
  - 宸叉柊澧?`step07_plot_raw_received_spectra.py`锛屽彲鐩存帴浠?`DEVICE-1-withAg-P1_hdr_curves.csv` 鎻愬彇 `Ag` 涓庡悓浣嶇疆鏍峰搧鐨勯暱/鐭洕鍏夊師濮?mean counts锛屽湪瀵规暟鍧愭爣涓婄粯鍒垛€滃厜璋变华瀹為檯鏀跺埌鐨勫厜璋扁€濓紝涓嶅仛鏇濆厜褰掍竴鍖栥€佷笉鍋?HDR 鏉冮噸銆佷篃涓嶄箻浠讳綍鏍″噯绯绘暟
  - 宸叉湁 `step01_absolute_calibration.py`锛屽彲灏嗘牱鍝佷笌閾堕暅鍘熷璁℃暟杞崲涓虹粷瀵瑰弽灏勭巼
  - 宸叉湁 `step01b_cauchy_extrapolation.py`锛屽彲鍩轰簬 [LIT-0001] 鐨?`ITO/CsFAPI` 鏁板瓧鍖栨姌灏勭巼鏇茬嚎鐢熸垚 `750-1100 nm` 鐨?CsFAPI 鎵╁睍 `n-k` 涓棿浠?
  - 宸叉湁 `step02_tmm_inversion.py`锛屽彲璇诲彇鐩爣鍙嶅皠鐜囥€両TO 鑹叉暎鍜?CsFAPI 鎵╁睍 `n-k` 涓棿浠讹紝鎵ц鍖呭惈 50/50 BEMA 绮楃硻搴︺€両TO 鑹叉暎鍚告敹琛ュ伩銆佸畯瑙傚帤搴︿笉鍧囧寑鎬ч珮鏂钩鍧囥€丳VK 鑹叉暎鏂滅巼鎵板姩涓?NiOx 瀵勭敓鍚告敹鐨勫叚鍙傛暟 `d_bulk + d_rough + ito_alpha + sigma_thickness + pvk_b_scale + niox_k` 鑱斿悎鍙嶆紨
  - 宸叉湁 `step03_batch_fit_samples.py`锛屽彲瀵?OneDrive 鍘熷鏍峰搧鐩綍涓殑澶氫綅缃?CSV 鍋氱粺涓€缁濆鍙嶅皠鐜囨牎鍑嗐€佸叚鍙傛暟鎵归噺鎷熷悎銆佸崟鏍峰搧鍥惧鍑哄拰姹囨€昏〃鐢熸垚
  - 宸叉湁 `step03_forward_simulation.py`锛屽彲鍥哄寲 Phase 03 鍏弬鏁版渶浼樺熀绾匡紝鍦?`850-1500 nm` 娉㈡鍓嶅悜棰勬祴 `SAM/PVK` 鐣岄潰绌烘皵闅欏缁濆鍙嶅皠鐜?`R` 涓庡樊鍒嗗弽灏勭巼 `螖R` 鐨勫奖鍝?
  - 宸叉湁 `step04a_air_gap_diagnostic.py`锛屽彲鍩轰簬 `test_data/good-21.csv` 涓?`test_data/bad-23.csv` 瀹屾垚缁濆鍙嶅皠鐜囨爣瀹氥€? 鍙傛暟/7 鍙傛暟瀵规瘮鎷熷悎銆佸樊鍒嗘寚绾规瘮瀵逛笌绌烘皵闅欐敹鏁涜瘖鏂?
  - 宸叉湁 `step04b_air_gap_localization.py`锛屽彲鍩轰簬 `test_data/good-21.csv` 涓?`test_data/bad-20-2.csv` 瀹屾垚绌烘皵闅欑┖闂村畾浣嶅姣斾笌鏉愭枡鍙傛暟寮涜鲍璇婃柇
  - 宸叉柊澧?`src/core/hdr_absolute_calibration.py`锛屽彲鎵弿 OneDrive 娴嬭瘯鐩綍銆佷粠 `.spe` 鍏冩暟鎹彁鍙栨洕鍏夋椂闂淬€佸閲嶅閲囬泦鍋氬潎鍊兼彁绾€佹墽琛?Bit-Agnostic Cross-fade HDR 铻嶅悎锛屽苟瀵煎嚭缁濆鍙嶅皠鐜?QA 鍥?琛?
  - 宸叉柊澧?`step06_single_sample_hdr_absolute_calibration.py`锛屽彲瀵?`DEVICE-1-withAg` 涓庡搴?`Ag_mirro` 缁勬墽琛屽崟鏍锋湰 HDR Dry Run锛岃緭鍑哄埌绯荤粺涓存椂鐩綍
  - 宸叉柊澧?`step06_batch_hdr_calibration.py`锛屽彲瀵?`0409/cor` 鐩綍涓嬪叏閮ㄦ牱鏈墽琛?HDR 缁濆鏍″噯鎵瑰鐞嗭紝骞跺悓姝ュ啓鍑洪」鐩洰褰曚笌 OneDrive 鍘熷潃瀛樻。
  - 宸叉湁 `diagnostics_shape_mismatch.py`锛屽彲鍦ㄧ嫭绔嬫矙鐩掍腑瀵?ITO 杩戠孩澶栧惛鏀躲€佸帤搴︿笉鍧囧寑鎬у拰 PVK 鑹叉暎鏂滅巼鍋氬舰鐘剁暩鍙樿瘖鏂?
  - 宸叉湁 `step02_digitize_fapi_optical_constants.py`锛屽彲浠?`LIT-0001` 鐨?Fig. 2 鍘熷浘鏁板瓧鍖栨彁鍙?FAPI 鐨?`n/魏` 鏇茬嚎骞惰緭鍑?QA 鍥?
  - 宸叉湁 `step02_digitize_csfapi_optical_constants.py`锛屽彲浠?`LIT-0001` 鐨?Fig. 3 鍘熷浘鏁板瓧鍖栨彁鍙?CsFAPI 鐨?`n/魏` 鏇茬嚎骞惰緭鍑?QA 鍥?
  - 宸叉湁 `step05_parse_ellipsometry_markdown.py`锛屽彲浠?`resources/n-kdata/*/full.md` 瑙ｆ瀽妞亸鎶ュ憡骞舵瀯寤?`materials_master_db.json`
  - 宸叉湁 `step05b_verify_against_pdf.py`锛屽彲鐢ㄥ師濮?PDF 浜ゅ弶楠岃瘉鏉愭枡鏁版嵁搴撲腑鐨勫帤搴︺€丷MSE銆佹尝娈佃寖鍥翠笌妯″瀷瀹屾暣鎬?
  - 宸叉湁 `step05c_build_aligned_nk_stack.py`锛屽彲鐢熸垚 `400-1100 nm / 1 nm` 鐨勫叏鏍堝榻?`n-k` 琛?`aligned_full_stack_nk.csv`
  - 宸叉湁 `src/core/full_stack_microcavity.py`锛屽彲鍩轰簬 `aligned_full_stack_nk.csv` 鏋勫缓 `Baseline / Case A / Case B / Front / Back` 浜旂被鍏ㄥ櫒浠跺井鑵斿爢鏍堬紝骞舵毚闇?`forward_model_for_fitting()` 浣滀负鍚庣画 LM 鐩爣鍑芥暟鍏ュ彛
  - 宸叉湁 `step06_dual_mode_microcavity_sandbox.py`锛屽彲鎵弿 `d_air = 0-50 nm`锛岃緭鍑哄弻妯″紡 `R / 螖R` 鎸囩汗瀛楀吀銆?0 nm 瀵规瘮鍥惧拰 2D 闆疯揪鐑姏鍥?
  - 宸叉湁 `step07_orthogonal_radar_and_baseline.py`锛屽彲杈撳嚭 pristine 鍏ㄨ氨涓夊垎鍖哄熀鍑嗗浘銆丗ront/Back 姝ｄ氦闆疯揪鍥句笌 `Phase 07` 鎸囩汗瀛楀吀
  - 宸叉柊澧?`src/core/phase07_dual_window.py`锛屽彲鍩轰簬 `aligned_full_stack_nk.csv` 鏋勫缓 `Glass / ITO / NiOx / SAM / PVK / PVK-C60 Roughness / C60 / Ag(or Air)` Phase 07 鍫嗘爤锛屾墽琛?C60 瀹堟亽绾︽潫銆佸弻绐楀姞鏉冩畫宸€乣d_bulk` 鍚庣獥 basin 鎵弿銆丏E 鍏ㄥ眬鎼滅储銆佸眬閮?least-squares 绮句慨涓?Phase 07 璇婃柇鍑哄浘
  - 宸叉柊澧?`step07_dual_window_inversion.py`锛屽彲浼樺厛璇诲彇鍘熷澶氭洕鍏夌洰褰曞苟澶嶇敤 Phase 06 HDR 閫昏緫锛屾垨鐩存帴娑堣垂 `*_hdr_curves.csv`锛岀粺涓€钀界洏涓?`fit_input -> fit_summary / fit_curve / optimizer_log / 4 寮犺瘖鏂浘`
  - 宸叉柊澧?`step08_theoretical_tmm_modeling.py`锛屽彲璇诲彇 `phase07_fit_summary.csv` 涓庡搴?`fit_input`锛屽喕缁?Phase 07 鏈€浼樺弬鏁板苟閲嶅缓鐞嗚鍙嶅皠鐜囥€佸墠琛ㄩ潰鏁ｅ皠鍥犲瓙鍜屽悗绐?z-score 瀵规瘮锛岀粺涓€钀界洏涓?`phase08_theory_curve / phase08_theory_summary / phase08_source_manifest / theory_vs_measured 鍥綻
  - 宸查噸鏋?`step08_build_audit_slide_deck.py`锛屽彲杈撳嚭鏇村鐨勫紩鐢ㄥ畾浣嶅浘鐢诲竷骞跺鍙充晶鏍囩鍋氳竟鐣屽す绱э紝閬垮厤瀹¤ deck 涓殑闀挎爣绛捐瑁佸垏
  - 宸查噸鏋?`results/slides/phase08_reference_audit/assets/deck.js` 涓?`theme.css`锛屽彲鍦ㄦ棤 `Reveal` 鎴栨棤 `KaTeX` 鐨勭幆澧冧笅鑷姩闄嶇骇锛屽苟淇濈暀鍙鐨勬湰鍦板璁″睍绀?
  - 宸查噸鐢?`results/slides/phase08_reference_audit/assets/value_locator_nk.svg` 涓?`value_locator_reflectance.svg`锛屼笌鏂扮殑鑴氭湰杈撳嚭鐢诲竷淇濇寔涓€鑷?
  - 宸叉柊澧?`stepA1_pristine_baseline.py`锛屽彲涓ユ牸鍩轰簬 `aligned_full_stack_nk.csv` 鍜屽父鏁扮幓鐠?`n=1.515, k=0` 鐢熸垚 `R_front / R_stack / R_total` 鐨?pristine baseline decomposition锛屽苟杈撳嚭涓夋洸绾垮浘銆佷笁鍖哄浘涓庢爣鍑嗘棩蹇?
  - 宸叉柊澧?`stepA1_1_pvk_seam_audit.py`锛屽彲鍥寸粫 `749/750 nm` 瀵?PVK seam 鍋氬眬閮?n-k/eps/瀵兼暟瀹¤銆佷笂娓镐笁婧愯拷婧€佺畝鍖栧爢鏍堟晱鎰熸€ф瘮杈冦€丄g 缁堢杈圭晫瀵圭収涓庝唬鐮佽矾寰勬牳鏌?
  - 宸叉柊澧?`stepA1_2_build_pvk_surrogate_v2.py`锛屽彲鍦ㄤ笉瑕嗙洊 v1 鏉愭枡琛ㄧ殑鍓嶆彁涓嬶紝瀵?PVK 鐨?`740-780 nm` band-edge 鍖哄煙鎵ц灞€閮?surrogate rebuild锛屽苟杈撳嚭 `aligned_full_stack_nk_pvk_v2.csv`銆佸€欓€夎繃娓″甫鎸囨爣琛ㄤ笌 v1/v2 QA 鍥?
 - 宸叉柊澧?`stepA1_2_rerun_pristine_with_pvk_v2.py`锛屽彲澶嶇敤 Phase A-1 pristine decomposition 鍙ｅ緞锛岀敤 `PVK surrogate v2` 閲嶈窇 `R_front / R_stack / R_total`锛屽苟杈撳嚭 v1/v2 鍏ㄨ氨涓庡眬閮ㄥ鐓?
 - 宸叉柊澧?`stepA2_pvk_thickness_scan.py`锛屽彲鍩轰簬 `aligned_full_stack_nk_pvk_v2.csv` 鎵弿 `d_PVK = 500-900 nm`銆佽緭鍑?`R_stack / R_total / 螖R` 鐑姏鍥俱€乸eak/valley tracking 涓庣壒寰佹眹鎬昏〃
  - 宸叉柊澧?`stepA_local_pvk_thickness_window.py`锛屽彲鍦ㄥ悓涓€ `PVK surrogate v2` 涓?nominal 鍏ㄥ櫒浠跺嚑浣曚笅锛屼粎鎵弿 `d_PVK = 675-725 nm / 1 nm`锛岃緭鍑哄眬閮ㄥ帤搴﹁捣浼忓搴旂殑 `R_total / 螖R_total` 鎸囩汗鍥俱€佸熀纭€涓夌獥鍙?RMS 鎽樿涓庢眹鎶ヨ祫浜?
  - 宸叉柊澧?`stepD2b_explain_feature_pipeline.py`锛屽彲鐩存帴璇诲彇 `phaseD1_rtotal_database.csv`銆乣phaseD2_quantitative_feature_database.csv`銆乣phaseD2_family_templates.csv` 涓?`PHASE_D2_REPORT.md`锛岃緭鍑?D-2 鐗瑰緛鎻愬彇娴佺▼瑙ｉ噴鍥俱€佸師濮嬭氨 vs 鐗瑰緛璺敱瀵规瘮鍥俱€佷簲绫荤壒寰佹潵婧愭€昏鍥句笌缁勪細璁茬鏂囨锛涜鑴氭湰涓嶅仛鏂扮殑鐗╃悊浠跨湡锛屽彧鍋氭眹鎶ュ眰淇℃伅閲嶇粍
  - 宸插缓绔?`results/report/` 姹囨姤璧勪骇灞傦紝骞惰ˉ榻?`Phase A-1.2` 涓?`Phase A-2` 鐨勭簿閫?CSV / PNG / Markdown 鎶ュ憡
  - 宸叉柊澧?`stepB1_rear_bema_sandbox.py`锛屽彲鍦?`PVK/C60` 鍚庣晫闈㈡彃鍏ュ浐瀹?`50/50` Bruggeman BEMA 灞傘€佹墽琛屽帤搴﹀畧鎭掓壂鎻忓苟涓?`d_PVK` 鎸囩汗鍋氬鐓?
  - 宸叉柊澧?`stepA2_1_pvk_uncertainty_ensemble.py`锛屽彲鏋勫缓 `nominal / more_absorptive / less_absorptive` 涓夋垚鍛?PVK ensemble锛岄噸璺戜唬琛ㄦ€?thickness / rear-BEMA 瀛愰泦骞惰緭鍑?robustness summary
  - 宸叉柊澧?`stepB2_front_bema_sandbox.py`锛屽彲鍦ㄥ浐瀹?`SAM` 鍘氬害鍓嶆彁涓嬪紩鍏?`NiOx/PVK` front-side BEMA proxy锛岃緭鍑?front-only roughness 涓绘壂鎻忋€佷笌 thickness/rear-BEMA 鐨勬浜ゅ鐓э紝浠ュ強 uncertainty spot-check
  - 宸叉柊澧?`stepC1a_rear_air_gap_sandbox.py`锛屽彲鍦?`PVK/C60` 鍚庣晫闈㈡彃鍏ョ湡瀹?air gap锛岃緭鍑?low-gap 楂樺垎杈ㄤ富鎵弿銆丩OD 绮楄瘎浼般€乥ranch-aware tracking 鍜屼笌 thickness / rear-BEMA / front-BEMA 鐨勫洓鏈哄埗瀵圭収
  - 宸叉柊澧?`stepC1b_front_air_gap_sandbox.py`锛屽彲鍦?`SAM/PVK` 鍓嶇晫闈㈡彃鍏ョ湡瀹?air gap锛岃緭鍑?low-gap 楂樺垎杈ㄤ富鎵弿銆佸墠/杩囨浮/鍚庣獥鍒嗙獥鍝嶅簲銆丩OD 绮楄瘎浼般€乽ncertainty spot-check 涓庝簲鏈哄埗瀵圭収
  - 宸叉柊澧?`stepPPT_phaseAtoC_assets.py`锛屽彲鍩轰簬鐜版湁 `data/processed` 缁撴灉閲嶇粯涓€濂楃粺涓€椋庢牸鐨?`R_total-only` PPT 姹囨姤璧勪骇锛屽苟鍚屾鐢熸垚姣忛〉 `slide_text.md / source_manifest.md`
  - 宸叉柊澧?`stepD1_airgap_discrimination_database.py`锛屽彲鍦?realistic `d_PVK + front/rear roughness` 鑳屾櫙涓婄粺涓€鏋勫缓 `thickness nuisance / roughness nuisance / front-gap overlay / rear-gap overlay` 鐨?`R_total / Delta_R_total` 鍒ゅ埆鏁版嵁搴擄紝骞惰緭鍑?rear shift analysis銆乫eature atlas 涓庣畻娉曡璁虹敤 report 璧勪骇
  - 宸蹭骇鍑烘爣鍑嗕腑闂存枃浠?`data/processed/target_reflectance.csv` 涓?`data/processed/CsFAPI_nk_extended.csv`
  - 宸插畬鎴?Phase 02 褰㈢姸鐣稿彉璇婃柇锛屽綋鍓嶈瘉鎹寚鍚戯細ITO 杩戠孩澶栧惛鏀跺け鐪熸槸闀挎尝绔墭骞充笌鏁翠綋褰㈢姸澶遍厤鐨勪富瀵煎洜绱?
  - 宸插畬鎴?Phase 04 绌烘皵闅欏墠鍚戦娴嬶紝褰撳墠鍩虹嚎涓?`d_air = 2 nm` 涓?`5 nm` 鐨?`max(|螖R|)` 鍒嗗埆绾︿负 `0.538%` 涓?`1.347%`锛屽潎楂樹簬 `0.2%` 鍏稿瀷鍣０绾?
  - 宸插畬鎴?Phase 04a 绌烘皵闅欒瘖鏂矙鐩掞細鍦?`bad-23` 涓婂姞鍏?`d_air` 鍚庯紝`chi-square` 鐢?`0.03197` 闄嶈嚦 `0.01619`锛宍d_air` 鏀舵暃鍒扮害 `39.9 nm`锛屼絾浠嶆湭浣庝簬 `0.01`
  - 宸插畬鎴?Phase 04b 绌烘皵闅欑┖闂村畾浣嶏細瀵?`bad-20-2` 鐨?L1/L2/L3 涓変釜 7 鍙傛暟妯″瀷涓紝L3 (`SAM/PVK`) 鐨?`chi-square` 鏈€浣庯紝浣嗘潗鏂欏弬鏁伴攣姝绘椂浠嶆湭浼樹簬 6 鍙傛暟鍩虹嚎锛涢噴鏀炬潗鏂欏弬鏁板悗 `chi-square` 鍙繘涓€姝ラ檷鑷?`0.01932`
  - 宸插畬鎴?Phase 06 鍗曟牱鏈?HDR Dry Run锛氬 `DEVICE-1-withAg` 鐨?`150 ms / 2000 ms` 涓夐噸澶嶅拰 `Ag_mirro` 鐨?`500 us / 10 ms` 鍗曢噸澶嶅畬鎴愬潎鍊兼彁绾€丠DR 铻嶅悎鍜岀粷瀵规牎鍑?
  - 宸插畬鎴?Phase 06c 鍏ㄩ噺鎵瑰鐞嗭細`DEVICE-1-withAg`銆乣DEVICE-1-withoutAg`銆乣DEVICE-2-withAg`銆乣DEVICE-2-withoutAg` 鍏?`4` 涓牱鏈叏閮ㄦ垚鍔熻惤鐩橈紝鏃犲紓甯告姏鍑?
  - 宸插畬鎴?Phase 07 鍙岀獥鍙嶆紨棣栬疆鍐掔儫锛歚DEVICE-1-withAg-P1` 涓?`DEVICE-1-withoutAg-P1` 鍧囧彲浠?`hdr_curves` 鍏ュ彛瀹屾垚鎷熷悎銆佸啓鍑?`fit_input / fit_summary / fit_curve / optimizer_log / full_spectrum / dual_window_zoom / residual_diagnostics / rear_basin_scan`
  - 宸茬‘璁ゅ綋鍓嶅疄娴嬬獥鍙ｄ粎瑕嗙洊 `498.934-1055.460 nm`锛屾湭澶栨帹鍒?`400-498.934 nm` 鎴?`1055.460-1100 nm`
  - 宸茬‘璁?`850-1055 nm` 鍖洪棿鐨勬牱鍝佷笌閾堕暅閮藉嚑涔庡畬鍏ㄤ俊浠婚暱鏇濆厜锛屽洜姝よ繎绾㈠鍖哄苟闈炴湰娆?HDR 鎷兼帴涓绘垬鍦?
  - 宸叉槑纭毚闇查摱闀滅煭鏇濆厜寮傚父锛氭寜 `.spe` 鍏冩暟鎹殑鐪熷疄鏇濆厜鏃堕棿褰掍竴鍖栧悗锛宍Ag_mirro-500us` 鐩稿 `Ag_mirro-10ms` 鐨?`Counts/ms` 姣斿€间腑浣嶆暟绾︿负 `12.28`
- 褰撳墠鏈畬鎴愬唴瀹癸細
  - 灏氭湭鎶婂巻鍙茬洰褰曞畬鍏ㄨ縼绉诲埌 `AGENTS.md` 瑙勫畾鐨勬柊缁撴瀯
  - 灏氭湭褰㈡垚瑙勮寖鍖栫殑 Phase 鏃ュ織銆佽祫婧愮储寮曞拰缁撴瀯鍖栫粨鏋滃彴璐?
  - 灏氭湭灏?Phase 06 鎵归噺 HDR 杈撳叆瑙勮寖鍖栬縼绉诲埌 `data/raw/phase06/`
  - Phase 07 褰撳墠涓や緥鐪熷疄鏍锋湰閮藉瓨鍦ㄥ弬鏁拌创杈癸紝璇存槑鍙岀獥鏋舵瀯宸茶窇閫氾紝浣嗘潗鏂欏厛楠屼笌杈圭晫璁惧畾浠嶉渶缁х画鏀舵暃
  - Phase 08 鐩墠浠嶄互鈥滃浐瀹氬弬鏁板墠鍚戦噸寤?+ 瀹¤ deck 鏀舵暃鈥濅负涓伙紝灏氭湭寮曞叆鏂扮殑鐗╃悊鍏堥獙銆佸眰缁撴瀯鍙樹綋鎵弿鎴栬法鏍锋湰鍏变韩鍙傛暟绾︽潫
  - `Phase A-2.1` 宸插畬鎴?first-pass uncertainty propagation锛屼絾灏氭湭鎵╁睍鍒版洿楂樼淮鐨?surrogate family 鎴栧弬鏁板寲浠嬬數鍑芥暟涓嶇‘瀹氭€?
  - `Phase B-2` 褰撳墠浠嶆槸 front-side optical proxy锛岃€屼笉鏄畬鏁村寲瀛︾晫闈㈡ā鍨?
  - `Phase C-1a / C-1b` 褰撳墠浠嶆槸鍗曚晶 gap only 鐨?specular TMM 妯″瀷锛屼笉鍚暎灏勩€乨ual-gap 鎴?gap+BEMA 鑰﹀悎
  - `Phase D-1` 褰撳墠浠呰鐩?thickness / roughness / gap 涓夌被缁撴瀯鏈哄埗锛屽皻鏈撼鍏?composition variation銆佸疄楠屽櫔澹版ā鍨嬩笌鐪熷疄鍒嗙被鍣ㄨ缁?
  - `constant-glass vs dispersive-glass` 涓庡弬鏁板寲 band-edge dielectric model 浠嶆湭灞曞紑

## 2. Current Directory Tree

浠ヤ笅鐩綍鏍戝熀浜庡綋鍓嶄粨搴撳疄闄呯姸鎬佹暣鐞嗭紝浠呬繚鐣欏叧閿眰绾у拰鍏抽敭鏂囦欢銆?

```text
TMM-interference-spectrum/
鈹溾攢鈹€ AGENTS.md
鈹溾攢鈹€ requirements.txt
鈹溾攢鈹€ docs/
鈹?  鈹溾攢鈹€ LITERATURE_MAP.md
鈹?  鈹斺攢鈹€ PROJECT_STATE.md
鈹溾攢鈹€ src/
鈹?  鈹溾攢鈹€ core/
鈹?  鈹?  鈹溾攢鈹€ full_stack_microcavity.py
鈹?  鈹?  鈹溾攢鈹€ hdr_absolute_calibration.py
鈹?  鈹?  鈹斺攢鈹€ phase07_dual_window.py
鈹?  鈹斺攢鈹€ scripts/
鈹?      鈹溾攢鈹€ diagnostics_shape_mismatch.py
鈹?      鈹溾攢鈹€ step01_absolute_calibration.py
鈹?      鈹溾攢鈹€ step01b_cauchy_extrapolation.py
鈹?      鈹溾攢鈹€ step02_digitize_csfapi_optical_constants.py
鈹?      鈹溾攢鈹€ step02_digitize_fapi_optical_constants.py
鈹?      鈹溾攢鈹€ step02_tmm_inversion.py
鈹?      鈹溾攢鈹€ step03_batch_fit_samples.py
鈹?      鈹溾攢鈹€ step03_forward_simulation.py
鈹?      鈹溾攢鈹€ step04a_air_gap_diagnostic.py
鈹?      鈹溾攢鈹€ step04b_air_gap_localization.py
鈹?      鈹溾攢鈹€ step06_batch_hdr_calibration.py
鈹?      鈹溾攢鈹€ step06_single_sample_hdr_absolute_calibration.py
鈹?      鈹溾攢鈹€ step07_dual_window_inversion.py
鈹?      鈹溾攢鈹€ step07_plot_raw_received_spectra.py
鈹?      鈹溾攢鈹€ step07_orthogonal_radar_and_baseline.py
鈹?      鈹溾攢鈹€ step08_theoretical_tmm_modeling.py
鈹?      鈹溾攢鈹€ stepA1_pristine_baseline.py
鈹?      鈹溾攢鈹€ stepA1_1_pvk_seam_audit.py
鈹?      鈹溾攢鈹€ stepA1_2_build_pvk_surrogate_v2.py
鈹?      鈹溾攢鈹€ stepA1_2_rerun_pristine_with_pvk_v2.py
鈹?      鈹溾攢鈹€ stepA2_pvk_thickness_scan.py
鈹?      鈹溾攢鈹€ stepA_local_pvk_thickness_window.py
鈹?      鈹溾攢鈹€ stepA2_1_pvk_uncertainty_ensemble.py
鈹?      鈹溾攢鈹€ stepB1_rear_bema_sandbox.py
鈹?      鈹溾攢鈹€ stepB2_front_bema_sandbox.py
鈹?      鈹溾攢鈹€ stepC1a_rear_air_gap_sandbox.py
鈹?      鈹溾攢鈹€ stepC1b_front_air_gap_sandbox.py
鈹?      鈹溾攢鈹€ stepD1_airgap_discrimination_database.py
鈹?      鈹溾攢鈹€ stepD2_quantitative_feature_dictionary.py
鈹?      鈹斺攢鈹€ stepD2b_explain_feature_pipeline.py
鈹溾攢鈹€ data/
鈹?  鈹斺攢鈹€ processed/
鈹?      鈹溾攢鈹€ CsFAPI_nk_extended.csv
鈹?      鈹溾攢鈹€ phase03_batch_fit/
鈹?      鈹溾攢鈹€ phase04a/
鈹?      鈹溾攢鈹€ phase04b/
鈹?      鈹溾攢鈹€ phase04c/
鈹?      鈹溾攢鈹€ phase06/
鈹?      鈹溾攢鈹€ phase07/
鈹?      鈹溾攢鈹€ phase08/
鈹?      鈹溾攢鈹€ phaseA1/
鈹?      鈹溾攢鈹€ phaseA1_2/
鈹?      鈹溾攢鈹€ phaseA2/
鈹?      鈹溾攢鈹€ phaseA_local/
鈹?      鈹溾攢鈹€ phaseA2_1/
鈹?      鈹溾攢鈹€ phaseB1/
鈹?      鈹溾攢鈹€ phaseB2/
鈹?      鈹溾攢鈹€ phaseC1a/
鈹?      鈹溾攢鈹€ phaseC1b/
鈹?      鈹溾攢鈹€ phaseD1/
鈹?      鈹溾攢鈹€ phaseA1_seam_audit/
鈹?      鈹斺攢鈹€ target_reflectance.csv
鈹溾攢鈹€ resources/
鈹?  鈹溾攢鈹€ digitized/
鈹?  鈹?  鈹溾攢鈹€ phase02_fig2_fapi_optical_constants_digitized.csv
鈹?  鈹?  鈹斺攢鈹€ phase02_fig3_csfapi_optical_constants_digitized.csv
鈹?  鈹溾攢鈹€ n-kdata/
鈹?  鈹溾攢鈹€ pvk_ensemble/
鈹?  鈹溾攢鈹€ aligned_full_stack_nk.csv
鈹?  鈹溾攢鈹€ aligned_full_stack_nk_pvk_v2.csv
鈹?  鈹溾攢鈹€ materials_master_db.json
鈹?  鈹溾攢鈹€ GCC-1022绯诲垪xlsx.xlsx
鈹?  鈹溾攢鈹€ ITO_20 Ohm_105 nm_e1e2.mat
鈹?  鈹溾攢鈹€ CsFAPI_TL_parameters_and_formulas.md
鈹?  鈹斺攢鈹€ MinerU-0.13.1-arm64.dmg
鈹溾攢鈹€ results/
鈹?  鈹溾攢鈹€ figures/
鈹?  鈹?  鈹溾攢鈹€ phaseA2/
鈹?  鈹?  鈹溾攢鈹€ phaseA_local/
鈹?  鈹?  鈹溾攢鈹€ phaseA2_1/
鈹?  鈹?  鈹溾攢鈹€ phaseB1/
鈹?  鈹?  鈹溾攢鈹€ phaseB2/
鈹?  鈹?  鈹溾攢鈹€ phaseC1a/
鈹?  鈹?  鈹溾攢鈹€ phaseC1b/
鈹?  鈹?  鈹溾攢鈹€ phaseA1_2/
鈹?  鈹?  鈹溾攢鈹€ phaseA1_seam_audit/
鈹?  鈹?  鈹溾攢鈹€ phaseA1/
鈹?  鈹?  鈹溾攢鈹€ phase08/
鈹?  鈹?  鈹溾攢鈹€ phase07/
鈹?  鈹?  鈹?  鈹斺攢鈹€ phase07_raw_received_spectra_log.png
鈹?  鈹?  鈹溾攢鈹€ absolute_reflectance_interference.png
鈹?  鈹?  鈹溾攢鈹€ cauchy_extrapolation_check.png
鈹?  鈹?  鈹溾攢鈹€ diagnostic_shape_analysis.png
鈹?  鈹?  鈹溾攢鈹€ phase03_batch_fit/
鈹?  鈹?  鈹溾攢鈹€ phase02_fig2_fapi_optical_constants_digitized.png
鈹?  鈹?  鈹溾攢鈹€ phase02_fig2_fapi_optical_constants_overlay.png
鈹?  鈹?  鈹溾攢鈹€ phase02_fig3_csfapi_optical_constants_digitized.png
鈹?  鈹?  鈹溾攢鈹€ phase02_fig3a_csfapi_optical_constants_overlay.png
鈹?  鈹?  鈹溾攢鈹€ phase02_fig3b_csfapi_optical_constants_overlay.png
鈹?  鈹?  鈹溾攢鈹€ phase04_air_gap_prediction.png
鈹?  鈹?  鈹溾攢鈹€ phase04a_air_gap_diagnostic.png
鈹?  鈹?  鈹溾攢鈹€ phase04b_localization.png
鈹?  鈹?  鈹溾攢鈹€ phase04c_fingerprint_mapping.png
鈹?  鈹?  鈹溾攢鈹€ phase06_dual_mode_delta_r_40nm_850_1100.png
鈹?  鈹?  鈹溾攢鈹€ phase06_dual_mode_radar_map.png
鈹?  鈹?  鈹溾攢鈹€ phase07_baseline_3zones.png
鈹?  鈹?  鈹溾攢鈹€ phase07_orthogonal_radar.png
鈹?  鈹?  鈹斺攢鈹€ tmm_inversion_result.png
鈹?  鈹斺攢鈹€ logs/
鈹?      鈹溾攢鈹€ phase03_batch_fit/
鈹?      鈹溾攢鈹€ phaseA2/
鈹?      鈹溾攢鈹€ phaseA_local/
鈹?      鈹溾攢鈹€ phaseA2_1/
鈹?      鈹溾攢鈹€ phaseB1/
鈹?      鈹溾攢鈹€ phaseB2/
鈹?      鈹溾攢鈹€ phaseC1a/
鈹?      鈹溾攢鈹€ phaseC1b/
鈹?      鈹溾攢鈹€ phaseD1/
鈹?      鈹溾攢鈹€ phaseA1_2/
鈹?      鈹溾攢鈹€ phaseA1_seam_audit/
鈹?      鈹溾攢鈹€ phaseA1/
鈹?      鈹溾攢鈹€ phase08/
鈹?      鈹溾攢鈹€ phase07/
鈹?      鈹?  鈹斺攢鈹€ phase07_raw_received_spectra_log.md
鈹?      鈹溾攢鈹€ phase04c_fingerprint_mapping.md
鈹?      鈹溾攢鈹€ phase04a_air_gap_diagnostic.md
鈹?      鈹溾攢鈹€ phase04b_localization.md
鈹?      鈹溾攢鈹€ phase06_dual_mode_microcavity_sandbox.md
鈹?      鈹溾攢鈹€ phase07_orthogonal_radar_diagnostic.md
鈹?      鈹溾攢鈹€ phase02_shape_diagnostic_report.md
鈹?      鈹溾攢鈹€ phase02_fig2_fapi_digitization_notes.md
鈹?      鈹溾攢鈹€ phase02_fig3_csfapi_digitization_notes.md
鈹?  鈹斺攢鈹€ report/
鈹?      鈹溾攢鈹€ README.md
鈹?      鈹溾攢鈹€ report_manifest.csv
鈹?      鈹溾攢鈹€ phaseA1_2_pvk_surrogate_and_pristine/
鈹?      鈹溾攢鈹€ phaseA2_1_pvk_uncertainty_ensemble/
鈹?      鈹溾攢鈹€ phaseA2_pvk_thickness_scan/
鈹?      鈹溾攢鈹€ phaseA_local_thickness_window/
鈹?      鈹溾攢鈹€ phaseB1_rear_bema_sandbox/
鈹?      鈹溾攢鈹€ phaseB2_front_bema_sandbox/
鈹?      鈹溾攢鈹€ phaseC1a_rear_air_gap_sandbox/
鈹?      鈹溾攢鈹€ phaseC1b_front_air_gap_sandbox/
鈹?      鈹溾攢鈹€ phaseD1_airgap_discrimination_database/
鈹?      鈹溾攢鈹€ phaseD2_quantitative_feature_dictionary/
鈹?      鈹斺攢鈹€ ppt_phaseAtoC_assets/
鈹溾攢鈹€ test_data/
鈹?  鈹溾攢鈹€ sample.csv
鈹?  鈹溾攢鈹€ glass-1mm.csv
鈹?  鈹斺攢鈹€ Ag-mirro.csv
鈹斺攢鈹€ reference/
    鈹斺攢鈹€ Khan.../...
```

## 3. Structure Compliance Notes

褰撳墠浠撳簱涓庨」鐩骇 `AGENTS.md` 瑙勮寖鐩告瘮锛屽瓨鍦ㄤ互涓嬬粨鏋勫亸宸細

- `test_data/` 浠嶇劧鎵挎媴鍘熷娴嬮噺鏁版嵁鐩綍鑱岃矗锛屽悗缁簲杩佺Щ鎴栭噸鍛藉悕鍒?`data/raw/`
- `reference/` 鐩墠瀛樻斁璁烘枃鎷嗚В缁撴灉锛屾寜鏂拌鑼冩洿閫傚悎閫愭骞跺叆 `resources/references/`
- `src/core/` 宸插紑濮嬪缓绔嬶紝浣?`step01/step02/step04` 鐨勫ぇ閲忓鐢ㄩ€昏緫浠嶆暎钀藉湪 `src/scripts/`
- 椤圭洰鏍瑰凡鏈?`requirements.txt`锛屼絾浠嶇己姝ｅ紡 `README.md`
- `src/core/` 宸插紑濮嬪缓绔嬶紝浣嗙洰鍓嶅彧鎵胯浇 Phase 06 鐨?HDR 閫昏緫锛涙洿鏃╅樁娈电殑澶ч噺澶嶇敤浠ｇ爜浠嶆暎钀藉湪 `src/scripts/`
- 椤圭洰鏍瑰皻鏃?`README.md`

杩欎簺鍋忓樊褰撳墠涓嶄細闃绘柇鐜版湁娴佺▼锛屼絾灞炰簬鍚庣画闇€瑕佹敹鏁涚殑缁撴瀯鍊哄姟銆?

## 4. Script SOP

### 4.1 `step01_absolute_calibration.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step01_absolute_calibration.py`
- 涓昏鑱岃矗锛氬皢鏍峰搧鍜岄摱闀滄祴閲忚鏁拌浆鎹负 `850-1100 nm` 娉㈡鐨勭粷瀵瑰弽灏勭巼锛屽苟杈撳嚭鍥捐〃鍜屾爣鍑嗕腑闂?CSV

杈撳叆锛?
- `test_data/sample.csv`
  - 鏍峰搧娴嬮噺鍏夎氨
  - 绾﹀畾鏇濆厜鏃堕棿锛?00 ms
- `test_data/Ag-mirro.csv`
  - 閾堕暅娴嬮噺鍏夎氨
  - 绾﹀畾鏇濆厜鏃堕棿锛?5 ms
- `resources/GCC-1022绯诲垪xlsx.xlsx`
  - 鍘傚鎻愪緵鐨勯摱闀滅粷瀵瑰弽灏勭巼鍩哄噯

鏍稿績澶勭悊娴佺▼锛?
- 鑷姩璇嗗埆 CSV 鐨勬尝闀垮垪鍜屽己搴﹀垪
- 鎴彇 `850-1100 nm` 鐩爣娉㈡
- 瀵归摱闀滀俊鍙锋寜鏇濆厜鏃堕棿鍋氬綊涓€鍖?
- 灏嗗巶瀹堕摱闀滃熀鍑嗘彃鍊煎埌鏍峰搧娉㈤暱缃戞牸
- 璁＄畻缁濆鍙嶅皠鐜囷細
  - `R_abs = (S_sample / S_mirror_norm) * R_mirror_ref`
- 瀵瑰弽灏勭巼鏇茬嚎鍋?Savitzky-Golay 骞虫粦

杈撳嚭锛?
- `data/processed/target_reflectance.csv`
  - 鍏抽敭鍒楃害瀹氳嚦灏戝寘鍚細
    - `Wavelength`
    - `R_smooth`
- `results/figures/absolute_reflectance_interference.png`

### 4.2 `step01b_cauchy_extrapolation.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step01b_cauchy_extrapolation.py`
- 涓昏鑱岃矗锛氫粠 [LIT-0001] Fig. 3 鐨勬暟瀛楀寲 `ITO/CsFAPI` 鎶樺皠鐜囨洸绾夸腑鎻愬彇閫忔槑鍖猴紝鐢?Cauchy 妯″瀷澶栨帹鍒?`1100 nm`锛岀敓鎴?step02 鍙洿鎺ユ秷璐圭殑鏍囧噯 `n-k` 涓棿浠?

杈撳叆锛?
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
  - [LIT-0001] Fig. 3 鐨勬暟瀛楀寲鍏夊甯告暟鏁版嵁
  - 鏈楠ゅ彧浣跨敤 `series = ITO/CsFAPI` 涓?`quantity = n` 鐨勬暟鎹?

褰撳墠妯″瀷鍋囪锛?
- 鍙埅鍙?`750-1000 nm` 鐨勮繎绾㈠閫忔槑鍖烘嫙鍚?Cauchy 妯″瀷
- Cauchy 妯″瀷鍐欎綔 `n(lambda) = A + B / (lambda_um^2)`
- 涓轰繚璇佹暟鍊肩ǔ瀹氭€э紝鎷熷悎鏃朵娇鐢?`lambda_um = wavelength_nm / 1000`
- `750-1100 nm` 鍐呯粺涓€寮哄埗 `k = 0`
- `1000-1100 nm` 涓鸿秴鍑?[LIT-0001] 鍘熷娴嬮噺绐楀彛鐨勮В鏋愬鎺ㄥ尯

杈撳嚭锛?
- `data/processed/CsFAPI_nk_extended.csv`
  - 鍒楃害瀹氾細
    - `Wavelength`
    - `n`
    - `k`
- `results/figures/cauchy_extrapolation_check.png`

### 4.3 `step02_tmm_inversion.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step02_tmm_inversion.py`
- 涓昏鑱岃矗锛氳鍙?`step01` 杈撳嚭鐨勭洰鏍囧弽灏勭巼銆両TO 鑹叉暎鍜?`step01b` 鐢熸垚鐨?CsFAPI 鎵╁睍 `n-k` 涓棿浠讹紝鎵ц鍖呭惈 BEMA 琛ㄩ潰绮楃硻搴︿慨姝ｃ€両TO 鑹叉暎鍚告敹琛ュ伩銆佸畯瑙傚帤搴︿笉鍧囧寑鎬ч珮鏂钩鍧囥€丳VK 鑹叉暎鏂滅巼鎵板姩涓?NiOx 瀵勭敓鍚告敹鐨勫叚鍙傛暟鑱斿悎鍙嶆紨

杈撳叆锛?
- `data/processed/target_reflectance.csv`
  - 鏉ヨ嚜 `step01`
- `data/processed/CsFAPI_nk_extended.csv`
  - 鏉ヨ嚜 `step01b`
  - 鐢ㄤ綔 PVK 灞傚湪 `850-1100 nm` 鐨勫鎶樺皠鐜囪緭鍏?
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`
  - ITO 浠嬬數鍑芥暟鏁版嵁搴?
  - 鑴氭湰鍏煎涓ょ被鎯呭喌锛?
    - MATLAB 鍙 MAT
    - 瀹為檯涓轰笁鍒楄〃鏍兼枃鏈?

褰撳墠妯″瀷鍋囪锛?
- 娉㈡锛歚850-1100 nm`
- 鍏ュ皠瑙掞細`0` 搴?
- 鐜荤拑鍓嶈〃闈㈡寜闈炵浉骞插鐞?
- 鍚庝晶钖勮啘鍫嗘爤鎸夌浉骞?TMM 澶勭悊
- ITO 鍘氬害鍥哄畾锛歚105 nm`
- NiOx 鍘氬害鍥哄畾锛歚20 nm`
- SAM 鍘氬害鍥哄畾锛歚2 nm`
- PVK 鍧椾綋鍘氬害 `d_bulk` 鎼滅储鑼冨洿锛歚400-500 nm`
- PVK 琛ㄩ潰绮楃硻灞傚帤搴?`d_rough` 鎼滅储鑼冨洿锛歚0-100 nm`
- ITO 鑹叉暎鍚告敹鍙傛暟 `ito_alpha` 鎼滅储鑼冨洿锛歚0.0-30.0`
- 瀹忚鍘氬害涓嶅潎鍖€鎬у弬鏁?`sigma_thickness` 鎼滅储鑼冨洿锛歚0.0-60.0 nm`
- PVK 鑹叉暎鏂滅巼缂╂斁鍙傛暟 `pvk_b_scale` 鎼滅储鑼冨洿锛歚0.1-3.0`
- NiOx 杩戠孩澶栧瘎鐢熷惛鏀跺弬鏁?`niox_k` 鎼滅储鑼冨洿锛歚0.0-0.5`
- PVK 閲囩敤 `step01b` 鐢熸垚鐨?CsFAPI 鎵╁睍 `n-k` 涓棿浠讹紝骞堕€氳繃绾挎€ф彃鍊兼槧灏勫埌鐩爣娉㈤暱缃戞牸
- 绮楃硻灞傞噰鐢?`50% PVK + 50% Air` 鐨?Bruggeman EMA 鏈夋晥浠嬭川妯″瀷
- ITO 鍦ㄨ繘鍏?TMM 涔嬪墠锛岄攣瀹氬疄閮?`n` 涓嶅彉锛屼粎瀵硅櫄閮?`k` 鏂藉姞閿氬畾鍦?`850-1100 nm` 鐨勪簩娆″闀胯壊鏁ｅ惛鏀剁缉鏀?
- 褰?`sigma_thickness >= 0.1 nm` 鏃讹紝瀵?`d_bulk` 鍦?`[-3蟽, +3蟽]` 涓婂仛 9 鐐圭鏁ｉ珮鏂姞鏉冨钩鍧囷紝浠ユā鎷熷厜鏂戝昂搴﹀唴鐨勫畯瑙傚帤搴︿笉鍧囧寑鎬?
- PVK 鑹叉暎鎵板姩浠?`1000 nm` 涓烘姌灏勭巼閿氱偣锛屼粎瀵?`n(位)-n(1000 nm)` 鐨勫彉鍖栭噺鏂藉姞 `pvk_b_scale` 缂╂斁
- NiOx 灞傚湪涓绘祦绋嬩腑鐢卞浐瀹氬疄閮?`2.1` 鍜屽彲鎷熷悎铏氶儴 `niox_k` 鏋勬垚
- 鐩稿共灞傚爢鏍堜负锛歚Glass -> ITO -> NiOx -> SAM -> PVK_Bulk -> PVK_Roughness -> Air`

鏍稿績澶勭悊娴佺▼锛?
- 璇诲彇鐩爣缁濆鍙嶅皠鐜?
- 璇诲彇 `step01b` 鐢熸垚鐨?CsFAPI 鎵╁睍 `n-k` 琛?
- 瑙ｆ瀽 ITO 鐨?`e1/e2` 鏁版嵁骞惰浆涓?`n + ik`
- 鏋勫缓 ITO 澶嶆姌灏勭巼鎻掑€煎櫒
- 鏍规嵁 `ito_alpha` 瀵?ITO 鐨勬秷鍏夌郴鏁?`k` 鍋氶暱娉㈠寮虹殑鑹叉暎鍚告敹鏀惧ぇ
- 鏋勫缓 PVK 澶嶆姌灏勭巼鎻掑€煎櫒
- 鏍规嵁 `pvk_b_scale` 鎵板姩 PVK 鐨勮繎绾㈠鑹叉暎鏂滅巼
- 鏍规嵁鎵板姩鍚庣殑鍧椾綋 PVK 澶嶄粙鐢靛父鏁拌绠?50/50 BEMA 绮楃硻灞傚鎶樺皠鐜?
- 鍔ㄦ€佹瀯寤?`2.1 + i*niox_k` 鐨?NiOx 澶嶆姌灏勭巼
- 璁＄畻瀹忚鍙嶅皠鐜囷細
  - 鐜荤拑鍓嶈〃闈㈣彶娑呭皵鍙嶅皠
  - 鐜荤拑鍚庢柟鍖呭惈绮楃硻灞傜殑钖勮啘鍫嗘爤鐩稿共 TMM
  - 鑻?`sigma_thickness` 闈為浂锛屽垯瀵瑰涓?`d_bulk` 閲囨牱鐐瑰仛楂樻柉鍔犳潈骞冲潎
  - 鍐嶆寜闈炵浉骞插己搴︾骇鑱斿叕寮忓悎鎴愭€诲弽灏勭巼
- 浣跨敤 `lmfit` 鐨?`leastsq` 鍋氬叚鍙傛暟鑱斿悎鍙嶆紨
- 杈撳嚭鏈€浣虫嫙鍚堝浘

杈撳嚭锛?
- `results/figures/tmm_inversion_result.png`
- 缁堢鎵撳嵃锛?
  - 鎷熷悎鍘氬害
  - `chi-square`
  - 浼樺寲鐘舵€?

### 4.4 `step02_digitize_fapi_optical_constants.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step02_digitize_fapi_optical_constants.py`
- 涓昏鑱岃矗锛氫粠 `LIT-0001` 鐨?Fig. 2 鍘熷浘涓彁鍙?FAPI 鐨勬姌灏勭巼 `n` 涓庢秷鍏夌郴鏁?`魏` 涓や釜瀛愬浘鏁版嵁锛屽苟杈撳嚭鍗曚竴 CSV 涓?QA 鍥?

杈撳嚭锛?
- `resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv`
- `results/figures/phase02_fig2_fapi_optical_constants_digitized.png`
- `results/figures/phase02_fig2_fapi_optical_constants_overlay.png`
- `results/logs/phase02_fig2_fapi_digitization_notes.md`

### 4.5 `step03_batch_fit_samples.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step03_batch_fit_samples.py`
- 涓昏鑱岃矗锛氬 OneDrive 鍘熷鏍峰搧鐩綍涓殑澶氫綅缃?CSV 閫愭枃浠舵墽琛岀粷瀵瑰弽灏勭巼鏍″噯銆佸叚鍙傛暟鎷熷悎銆佸崟鏍峰搧鍥惧鍑哄拰姹囨€昏〃鐢熸垚

杈撳叆锛?
- `/Users/luxin/Library/CloudStorage/OneDrive-鍏变韩鐨勫簱-onedrive/Data/PL/2026/0403/cor/data-0403/*.csv`
- `test_data/Ag-mirro.csv`
- `resources/GCC-1022绯诲垪xlsx.xlsx`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`
- `data/processed/CsFAPI_nk_extended.csv`

杈撳嚭锛?
- `results/figures/phase03_batch_fit/*.png`
- `data/processed/phase03_batch_fit/*.csv`
- `results/logs/phase03_batch_fit/phase03_batch_fit_summary.csv`
- `results/logs/phase03_batch_fit/phase03_batch_fit_pivot.csv`
- `/Users/luxin/Library/CloudStorage/OneDrive-鍏变韩鐨勫簱-onedrive/Data/PL/2026/0403/cor/data-0403/batch-fit-results/...`

### 4.6 `step02_digitize_csfapi_optical_constants.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step02_digitize_csfapi_optical_constants.py`
- 涓昏鑱岃矗锛氫粠 `LIT-0001` 鐨?Fig. 3 鍘熷浘涓彁鍙?CsFAPI 鐨勬姌灏勭巼 `n` 涓庢秷鍏夌郴鏁?`魏` 涓や釜瀛愬浘鏁版嵁锛屽苟杈撳嚭鍗曚竴 CSV 涓?QA 鍥?

杈撳嚭锛?
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `results/figures/phase02_fig3_csfapi_optical_constants_digitized.png`
- `results/figures/phase02_fig3a_csfapi_optical_constants_overlay.png`
- `results/figures/phase02_fig3b_csfapi_optical_constants_overlay.png`
- `results/logs/phase02_fig3_csfapi_digitization_notes.md`

### 4.7 `step03_forward_simulation.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step03_forward_simulation.py`
- 涓昏鑱岃矗锛氬浐鍖?Phase 03 鍏弬鏁版渶浼樺熀绾匡紝鍦?`850-1500 nm` 娉㈡鍓嶅悜鎵弿 `SAM/PVK` 鐣岄潰绌烘皵闅欏紩鍏ュ悗鐨勭粷瀵瑰弽灏勭巼 `R` 涓庡樊鍒嗗弽灏勭巼 `螖R`

杈撳叆锛?
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

鍥哄寲鍙傛暟锛?
- `d_bulk_base = 700.0 nm`
- `d_rough = 31.337 nm`
- `ito_alpha = 13.313`
- `sigma_thickness = 22.761 nm`
- `pvk_b_scale = 1.626`
- `niox_k = 0.455`

鏍稿績澶勭悊娴佺▼锛?
- 澶嶇敤 `step02_tmm_inversion.py` 鐨?ITO 鏁版嵁璇诲彇銆佷粙鐢靛父鏁拌浆 `n+k`銆両TO 闀挎尝鍚告敹琛ュ伩銆丅EMA 绮楃硻灞備笌鍘氱幓鐠冮潪鐩稿共鍚堟垚閫昏緫
- 瀵?`data/processed/CsFAPI_nk_extended.csv` 鍏堝仛 `<=1100 nm` 鐨勮〃鏍兼彃鍊?
- 瀵?`1100-1500 nm` 鐨?PVK 灏鹃儴鎶樺皠鐜囷紝鍦?`1050-1100 nm` 鐪熷疄琛ㄦ牸涓婃嫙鍚?`n(lambda)=A+B/lambda_um^2` 鐨?Cauchy 妯″瀷锛屽苟寮哄埗 `k = 0`
- 淇濇寔 `sigma_thickness` 鐨?`9` 鐐归珮鏂帤搴﹀钩鍧?
- 灏嗙浉骞插眰鍫嗘爤鍗囩骇涓猴細
  - `Glass -> ITO -> NiOx -> SAM -> Air_Gap -> PVK_Bulk -> PVK_Roughness -> Air`
- 鎵弿 `d_air = [0, 2, 5, 10, 50, 100] nm`
- 浠?`d_air = 0` 涓哄熀绾胯绠?`螖R = R_dair - R_0`

杈撳嚭锛?
- `results/figures/phase04_air_gap_prediction.png`
- 缁堢鎽樿锛?
  - `PVK >1100 nm` 澶栨帹鏄惁鎴愬姛
  - `Cauchy A/B` 鍙傛暟
  - `d_air = 2 nm` 涓?`5 nm` 鐨?`max(|螖R|)`
  - 鏄惁楂樹簬 `0.2%` 鍣０闃堝€?

### 4.8 `step04a_air_gap_diagnostic.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step04a_air_gap_diagnostic.py`
- 涓昏鑱岃矗锛氬 `test_data/good-21.csv` 涓?`test_data/bad-23.csv` 鍋氫唬琛ㄦ€х粷瀵瑰弽灏勭巼鏍囧畾銆? 鍙傛暟/7 鍙傛暟鎷熷悎瀵规瘮涓庣┖姘旈殭宸垎鎸囩汗璇婃柇

杈撳叆锛?
- `test_data/good-21.csv`
- `test_data/bad-23.csv`
- `test_data/Ag-mirro.csv`
- `resources/GCC-1022绯诲垪xlsx.xlsx`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

鏍稿績澶勭悊娴佺▼锛?
- 鍏堝鐢?`step01_absolute_calibration.py` 灏?`good-21` 涓?`bad-23` 鍘熷璁℃暟杞崲涓?`850-1100 nm` 鐨?`Measured Smooth`
- 瀵?`good-21` 杩愯瀹屾暣鍏弬鏁版嫙鍚堬紝鎻愬彇 `ito_alpha`銆乣pvk_b_scale`銆乣niox_k` 浣滀负 bad 鏍峰搧 7 鍙傛暟璇婃柇涓殑閿佸畾鏉愭枡鍙傛暟
- 瀵?`bad-23` 鍏堣繍琛屽叚鍙傛暟鍩虹嚎鎷熷悎锛屽啀杩愯浠呮斁寮€ `d_bulk`銆乣d_rough`銆乣sigma_thickness`銆乣d_air` 鐨勪竷鍙傛暟灞€閮ㄤ紭鍖?
- 绌烘皵闅欎綅缃樉寮忓浐瀹氫负 `SAM -> Air_Gap -> PVK`
- 杈撳嚭 `螖R_exp = R_bad - R_good` 涓?`螖R_theory = R_bad_7p_fit - R_good_6p_fit` 鐨勫樊鍒嗘寚绾瑰姣?
- 妫€鏌?`d_air` 鏄惁鍗″湪涓嬬晫/鍒濆€硷紝浠ュ強 `chi-square` 鏄惁鏀瑰杽鍒?`0.01` 浠ヤ笅

杈撳嚭锛?
- `data/processed/phase04a/good-21_calibrated.csv`
- `data/processed/phase04a/bad-23_calibrated.csv`
- `results/figures/phase04a_air_gap_diagnostic.png`
- `results/logs/phase04a_air_gap_diagnostic.md`

### 4.9 `step04b_air_gap_localization.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step04b_air_gap_localization.py`
- 涓昏鑱岃矗锛氬 `test_data/bad-20-2.csv` 鎵ц绌烘皵闅欑┖闂村畾浣嶅弽璇佹祴璇曪紝骞跺湪鏈€浣充綅缃笂閲婃斁鏉愭枡鍙傛暟鍋氳繘涓€姝ュ紱璞?

杈撳叆锛?
- `test_data/good-21.csv`
- `test_data/bad-20-2.csv`
- `test_data/Ag-mirro.csv`
- `resources/GCC-1022绯诲垪xlsx.xlsx`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

鏍稿績澶勭悊娴佺▼锛?
- 鍏堝鐢?04a 鐨勬爣瀹氶摼鐢熸垚 `good-21` 涓?`bad-20-2` 鐨?`Measured Smooth`
- 瀵?`good-21` 杩愯鍏弬鏁版嫙鍚堬紝鎻愬彇 `base_ito_alpha`銆乣base_pvk_b_scale` 涓?`base_niox_k`
- 瀵?`bad-20-2` 鐨?7 鍙傛暟妯″瀷鍒嗗埆娴嬭瘯涓夌绌烘皵闅欎綅缃細
  - `L1: Glass -> Air_Gap -> ITO`
  - `L2: ITO -> Air_Gap -> NiOx`
  - `L3: SAM -> Air_Gap -> PVK`
- 鍦ㄦ潗鏂欏弬鏁伴攣瀹氬埌 `good-21` 鐨勫墠鎻愪笅姣旇緝 L1/L2/L3 鐨?`chi-square` 涓?`d_air`
- 閫夊彇鏈€浣充綅缃悗锛屽啀閲婃斁 `ito_alpha`銆乣pvk_b_scale` 涓?`niox_k`锛屽苟鎶婁笁鑰呰竟鐣岄檺鍒跺湪 `good-21` 鍩哄噯鍊肩殑 `卤15%`

杈撳嚭锛?
- `data/processed/phase04b/good-21_calibrated.csv`
- `data/processed/phase04b/bad-20-2_calibrated.csv`
- `results/figures/phase04b_localization.png`
- `results/logs/phase04b_localization.md`

### 4.10 `src/core/hdr_absolute_calibration.py`

- 鏂囦欢浣嶇疆锛歚src/core/hdr_absolute_calibration.py`
- 涓昏鑱岃矗锛氫负 Phase 06 鎻愪緵鍙鐢ㄧ殑 HDR 缁濆鏍″噯鍏叡閫昏緫锛岄伩鍏嶅皢璺緞鎵弿銆乣.spe` 鏇濆厜鏃堕棿瑙ｆ瀽銆侀噸澶嶆眰鍧囧€煎拰 HDR 鎷兼帴鏁ｈ惤鍦ㄨ剼鏈眰

杈撳叆锛?
- OneDrive 鍘熷鐩綍涓殑 `-cor.csv / -cor.spe`
- `resources/GCC-1022绯诲垪xlsx.xlsx`

鏍稿績澶勭悊娴佺▼锛?
- 鎸夊墠缂€鍜屾洕鍏夋爣绛炬壂鎻忕洰鏍囩粍锛岀姝㈢‖缂栫爜鍖呭惈涓枃鏃堕棿鎴崇殑瀹屾暣鏂囦欢鍚?
- 浠?`.spe` XML 鍏冩暟鎹紭鍏堣鍙?`ExposureTime`銆佽儗鏅弬鑰冭矾寰勫拰 `FramesToStore`
- 灏嗗悓鏇濆厜閲嶅閲囬泦鍦?`Counts` 绾у埆姹傜畻鏈钩鍧囷紝褰㈡垚 `Mean_Counts`
- 鎸?`Counts / ms` 褰掍竴鍖栧緱鍒?`N_long` 涓?`N_short`
- 鍩轰簬闀挎洕鍏?`Cmax` 鏋勯€?`TH_lower = 0.75 * Cmax` 涓?`TH_upper = 0.90 * Cmax`
- 瀵归暱鏇濆厜璁℃暟鎵ц绾挎€?`W_long` 鏉冮噸铻嶅悎锛岀敓鎴?`HDR(Counts/ms)`
- 璇诲彇閾堕暅鐞嗚鍙嶅皠鐜囪〃骞舵彃鍊煎埌鐩爣娉㈤暱缃戞牸
- 杈撳嚭缁濆鍙嶅皠鐜囨洸绾裤€丠DR QA 鍥俱€佹渶澶х浉閭荤偣璺冲彉鍜屼竴鑷存€х粺璁?

### 4.11 `step06_single_sample_hdr_absolute_calibration.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step06_single_sample_hdr_absolute_calibration.py`
- 涓昏鑱岃矗锛氬 `DEVICE-1-withAg` 鐨勫崟鏍锋湰缁勬墽琛?Bit-Agnostic HDR Dry Run锛屽苟灏嗗浘琛ㄤ笌鎽樿杈撳嚭鍒扮郴缁熶复鏃剁洰褰?

杈撳叆锛?
- `D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-150ms-{1,2,3}*.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-2000ms-{1,2,3}*.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-500us-1*.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-10ms-1*.csv`
- `resources/GCC-1022绯诲垪xlsx.xlsx`

杈撳嚭锛?
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_hdr_diagnostic.png`
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_absolute_reflectance.png`
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_curve_table.csv`
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_summary.md`

### 4.12 `step06_batch_hdr_calibration.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step06_batch_hdr_calibration.py`
- 涓昏鑱岃矗锛氭壒閲忔壂鎻?OneDrive `0409/cor` 鐩綍涓殑鎵€鏈夋牱鏈墠缂€锛岀粺涓€澶嶇敤 `Ag_mirro` HDR 鍙傝€冿紝杈撳嚭椤圭洰鍐呮爣鍑嗙粨鏋滃拰 OneDrive 鍘熷潃瀛樻。

杈撳叆锛?
- `D:\onedrive\Data\PL\2026\0409\cor\*-cor.csv`
- `resources/GCC-1022绯诲垪xlsx.xlsx`

杈撳嚭锛?
- `data/processed/phase06_batch/[Sample_Prefix]_curve_table.csv`
- `data/processed/phase06_batch/phase06_batch_summary.csv`
- `results/figures/phase06_batch/[Sample_Prefix]_QA_plot.png`
- `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\[Sample_Prefix]_hdr_curves.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\[Sample_Prefix]_hdr_qa.png`
- `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\00_batch_summary_0409.csv`

### 4.13 `diagnostics_shape_mismatch.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/diagnostics_shape_mismatch.py`
- 涓昏鑱岃矗锛氬湪涓嶄慨鏀逛富娴佺▼鐨勫墠鎻愪笅锛屽鐢?`step02` 鐨勬暟鎹鍙栧拰 BEMA 鍩虹嚎妯″瀷锛屽鏉＄汗褰㈢姸鐣稿彉鐨勭墿鐞嗘潵婧愬仛璇婃柇

杈撳叆锛?
- `data/processed/target_reflectance.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

鏍稿績璇婃柇鎺㈤拡锛?
- Probe A锛氬 ITO 鐨勮繎绾㈠ `k` 鏂藉姞闀挎尝澧炲己缂╂斁锛屾祴璇?Drude 鍚告敹澶辩湡鍋囪
- Probe B锛氬 `d_bulk` 鍋氶珮鏂帤搴﹀钩鍧囷紝娴嬭瘯鍏夋枒鍐呭畯瑙傚帤搴︿笉鍧囧寑鎬?
- Probe C锛氭斁寮€ PVK 鐨?Cauchy `B` 鍙傛暟缂╂斁锛屾祴璇曡繎绾㈠鑹叉暎鏂滅巼鏄惁杩囧钩

杈撳嚭锛?
- `results/figures/diagnostic_shape_analysis.png`
- `results/logs/phase02_shape_diagnostic_report.md`

### 4.11 `step06_dual_mode_microcavity_sandbox.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step06_dual_mode_microcavity_sandbox.py`
- 涓昏鑱岃矗锛氱洿鎺ユ秷璐?`Phase 05c` 鐨?`aligned_full_stack_nk.csv`锛屽湪鍏ㄥ櫒浠跺嚑浣曚笅鏋勫缓 `Baseline / Case A / Case B` 鍙屾ā寮忓井鑵旂己闄锋寚绾瑰瓧鍏?

杈撳叆锛?
- `resources/aligned_full_stack_nk.csv`
- `resources/materials_master_db.json`
- `src/core/full_stack_microcavity.py`

鏍稿績澶勭悊娴佺▼锛?
- 鏍￠獙 `aligned_full_stack_nk.csv` 鏄惁婊¤冻 `400-1100 nm / 1 nm` 鐨勫畬鏁寸綉鏍煎拰鍥哄畾鍒楃害瀹?
- 鏍￠獙 `materials_master_db.json` 涓殑 `ITO / NIOX / C60` 鍘氬害鏄惁涓?`Phase 06` 鍙ｅ緞涓€鑷?
- 鍦ㄥ帤鐜荤拑鍓嶈〃闈㈤噰鐢?`Air -> Glass` 闈炵浉骞插弽灏勭骇鑱旓紝鍦ㄧ幓鐠冨悗渚ц杽鑶滃爢鏍堥噰鐢ㄧ浉骞?TMM
- 鏋勫缓涓夌灞傚簭锛?
  - `Baseline: Glass -> ITO -> NiOx -> PVK -> C60 -> Ag`
  - `Case A: Glass -> ITO -> NiOx -> PVK -> C60 -> Air_Gap -> Ag`
  - `Case B: Glass -> ITO -> NiOx -> PVK -> Air_Gap -> C60 -> Ag`
- 瀵?`d_air = 0-50 nm` 鍋氶€?nm 鎵弿锛岃緭鍑?`R(lambda)` 鍜?`螖R(lambda) = R(d_air) - R(0)`
- 鐢熸垚 `d_air = 40 nm` 鐨勫弻妯″紡闀挎尝宸垎瀵规瘮鍥撅紝浠ュ強 `Case A / Case B` 鍙?panel 闆疯揪鐑姏鍥?

杈撳嚭锛?
- `data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv`
- `results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png`
- `results/figures/phase06_dual_mode_radar_map.png`
- `results/logs/phase06_dual_mode_microcavity_sandbox.md`

### 4.12 `step07_orthogonal_radar_and_baseline.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step07_orthogonal_radar_and_baseline.py`
- 涓昏鑱岃矗锛氬湪 `Phase 06` 鍏ㄦ爤璇昏〃妗嗘灦涓婏紝鏋勫缓 pristine 鍏ㄨ氨涓夊垎鍖哄熀鍑嗗浘涓?`front/back` 姝ｄ氦鐣岄潰鎺激闆疯揪

杈撳叆锛?
- `resources/aligned_full_stack_nk.csv`
- `resources/materials_master_db.json`
- `src/core/full_stack_microcavity.py`

鏍稿績澶勭悊娴佺▼锛?
- 閫氳繃 `forward_model_for_fitting(wavelengths_nm, d_air_nm, interface_type)` 鏆撮湶鏍囧噯绾疄鏁板墠鍚戞帴鍙ｏ紝浣滀负鍚庣画 LM 鐩爣鍑芥暟鎻掓Ы
- 鐢?`d_air = 0 nm` 鐢熸垚 pristine 鍏ㄨ氨缁濆鍙嶅皠鐜囧熀鍑嗭紝骞舵寜 `400-650 / 650-810 / 810-1100 nm` 涓夊垎鍖虹粯鍒惰儗鏅殧绂诲浘
- 瀵?`front (NiOx/PVK)` 涓?`back (PVK/C60)` 鍒嗗埆鎵ц `d_air = 0-50 nm` 鎵弿锛岃緭鍑哄叡浜壊鏍囩殑鍙?panel `螖R` 闆疯揪鍥?
- 鐢熸垚 `Phase 07` 鎸囩汗瀛楀吀涓庡垎鍖鸿瘖鏂棩蹇楋紝骞舵樉寮忔瘮杈?Zone 1 涓嬪墠鍚庣晫闈俊鍙峰己寮?

杈撳嚭锛?
- `data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv`
- `results/figures/phase07_baseline_3zones.png`
- `results/figures/phase07_orthogonal_radar.png`
- `results/logs/phase07_orthogonal_radar_diagnostic.md`

### 4.13 `step07_dual_window_inversion.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step07_dual_window_inversion.py`
- 鏍稿績渚濊禆锛歚src/core/phase07_dual_window.py`銆乣src/core/hdr_absolute_calibration.py`
- 涓昏鑱岃矗锛氬皢 `Phase 06` HDR 缁濆鏍囧畾涓?`Phase 07` 鍙岀獥鑱斿悎鍙嶆紨鎺ユ垚鏍囧噯娴佹按绾匡紝骞舵樉寮忚緭鍑哄弽婕斿彴璐︺€佸浘琛ㄥ拰鍛婅

杈撳叆锛?
- `test_data/phase7_data/*_hdr_curves.csv`
  - 褰撳墠浠撳簱鍐呭凡楠岃瘉鐨勭洿鎺ュ叆鍙?
- 鎴?`test_data/phase7_data/*-cor.csv + *.spe`
  - 鑻ュ瓨鍦ㄥ師濮嬪鏇濆厜鏁版嵁锛屽垯浼樺厛澶嶇敤 `Phase 06` HDR 鍏叡妯″潡鐜板満閲嶅缓 `R_abs`
- `resources/aligned_full_stack_nk.csv`
- `resources/GCC-1022绯诲垪xlsx.xlsx`

鏍稿績澶勭悊娴佺▼锛?
- 鎵弿杈撳叆鐩綍锛屼紭鍏堣瘑鍒師濮嬪鏇濆厜缁勶紱鑻ョ己灏戝師濮嬫枃浠讹紝鍒欏洖閫€鍒?`*_hdr_curves.csv`
- 缁熶竴鏀瑰啓涓?`data/processed/phase07/fit_inputs/*_fit_input.csv`锛屽瓧娈佃嚦灏戝寘鍚細
  - `Wavelength_nm`
  - `Absolute_Reflectance`
  - `window_label`
  - `with_ag`
- 浣跨敤 `src/core/phase07_dual_window.py` 鏋勫缓 `Glass / ITO / NiOx / SAM / PVK / PVK-C60 Roughness / C60 / Ag(or Air)` 鍏ㄦ爤妯″瀷
- 鍦ㄨ繍琛屾椂瀵?`d_rough` 鎵ц C60 瀹堟亽鍓ョ锛?
  - `d_C60_bulk = max(0, 15 - 0.5 * d_rough)`
- 浠呭 `500-650 nm` 涓?`860-1055 nm` 鎵ц鍔犳潈浼樺寲锛宍650-860 nm` 浠呬繚鐣欎负 PL/澶遍厤璇婃柇鍖?
- 鍏堝 `d_bulk` 鍋氬悗绐?basin 鎵弿锛屽啀鎵ц DE 鍏ㄥ眬鎼滅储鍜屽眬閮?least-squares 绮句慨
- 杈撳嚭閫愭尝闀挎嫙鍚堣〃銆佸崟鏍锋湰姹囨€昏〃銆佷紭鍖栨棩蹇楀強 4 寮犲浘

杈撳嚭锛?
- `data/processed/phase07/phase07_source_manifest.csv`
- `data/processed/phase07/phase07_fit_summary.csv`
- `data/processed/phase07/fit_results/*_fit_curve.csv`
- `data/processed/phase07/fit_results/*_fit_summary.csv`
- `results/figures/phase07/*_full_spectrum.png`
- `results/figures/phase07/*_dual_window_zoom.png`
- `results/figures/phase07/*_residual_diagnostics.png`
- `results/figures/phase07/*_rear_basin_scan.png`
- `results/logs/phase07/*_optimizer_log.md`

### 4.14 `step08_theoretical_tmm_modeling.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/step08_theoretical_tmm_modeling.py`
- 鏍稿績渚濊禆锛歚src/core/phase07_dual_window.py`
- 涓昏鑱岃矗锛氬喕缁?`Phase 07` 鏈€浼樺弬鏁板苟鍦ㄥ疄娴嬬┖闂撮噸寤虹悊璁哄弽灏勭巼锛屽舰鎴?`Phase 08` 鐨勬壒閲?TMM 鍓嶅悜寤烘ā鍩虹嚎

杈撳叆锛?
- `data/processed/phase07/phase07_fit_summary.csv`
- `data/processed/phase07/fit_inputs/*_fit_input.csv`
- `resources/aligned_full_stack_nk.csv`

鏍稿績澶勭悊娴佺▼锛?
- 閫愭牱鏈鍙?`Phase 07 fit_summary + fit_input`
- 澶嶇敤 `calc_macro_reflectance()` 閲嶅缓鍏ㄦ爤鐗╃悊鍙嶅皠鐜?
- 澶嶇敤 `apply_front_scattering_observation_model()` 鎶婄墿鐞嗘洸绾挎槧灏勫洖 collected reflectance
- 瀵瑰悗绐楅澶栬緭鍑?`z-score` 鐞嗚瀵规瘮涓庡鏁扮浉鍏虫€э紝妫€鏌ュ共娑夊舰璨屾槸鍚﹁淇濈暀
- 鎵归噺鍐欏嚭鐞嗚鏇茬嚎琛ㄣ€佹壒娆℃憳瑕併€佹潵婧愭竻鍗曞拰鐞嗚瀵规瘮鍥?

杈撳嚭锛?
- `data/processed/phase08/phase08_theory_summary.csv`
- `data/processed/phase08/phase08_source_manifest.csv`
- `data/processed/phase08/theory_curves/*_theory_curve.csv`
- `results/figures/phase08/*_theory_vs_measured.png`
- `results/logs/phase08/phase08_theoretical_tmm_modeling.md`

### 4.15 `stepA1_pristine_baseline.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepA1_pristine_baseline.py`
- 鏍稿績渚濊禆锛歚src/core/full_stack_microcavity.py`
- 涓昏鑱岃矗锛氬缓绔嬮浂缂洪櫡 pristine baseline decomposition锛屾樉寮忔媶鍒?`R_front / R_stack / R_total`

杈撳叆锛?
- `resources/aligned_full_stack_nk.csv`
  - 浣滀负鏈疆鍞竴 `n-k` 杈撳叆鏉ユ簮

鏍稿績澶勭悊娴佺▼锛?
- 鏍￠獙 `aligned_full_stack_nk.csv` 鐨勬潗鏂欏垪鍜?`400-1100 nm / 1 nm` 娉㈤暱缃戞牸
- 寮哄埗瑕嗙洊鐜荤拑涓哄父鏁?`n_glass = 1.515`, `k_glass = 0`
- 璁＄畻 `Air / Glass` 鍓嶈〃闈?Fresnel 鍙嶅皠 `R_front`
- 璁＄畻 `Glass -> ITO -> NiOx -> SAM -> PVK -> C60 -> Ag(100 nm) -> Air` 鐨勭浉骞插弽灏?`R_stack`
- 鐢ㄥ帤鐜荤拑寮哄害绾ц仈璁＄畻 `R_total`
- 杈撳嚭涓夋洸绾垮垎瑙ｅ浘銆佷笁鍖哄熀绾垮浘鍜?Markdown 缁撴灉璇存槑

杈撳嚭锛?
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `results/figures/phaseA1/phaseA1_pristine_decomposition.png`
- `results/figures/phaseA1/phaseA1_pristine_3zones.png`
- `results/logs/phaseA1/phaseA1_pristine_baseline.md`

### 4.16 `stepA1_1_pvk_seam_audit.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepA1_1_pvk_seam_audit.py`
- 鏍稿績渚濊禆锛歚src/core/full_stack_microcavity.py`
- 涓昏鑱岃矗锛氬 `749/750 nm` 闄勮繎鐨?PVK seam 鍋氭硶鍖诲紡瀹¤锛岀‘璁ゆ帴缂濇潵婧愩€佺粨鏋勬斁澶ч摼璺笌杈圭晫鏉′欢褰卞搷

杈撳叆锛?
- `resources/aligned_full_stack_nk.csv`
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `src/scripts/step05c_build_aligned_nk_stack.py`

鏍稿績澶勭悊娴佺▼锛?
- 鎶藉彇 `730-770 nm` 鐨?`n_PVK / k_PVK / eps1 / eps2` 涓庝竴闃跺鏁?
- 瀵圭収 digitized / extended / aligned 涓変唤 PVK 鏁版嵁锛屽畾浣?seam 鐨勫紩鍏ユ楠?
- 姣旇緝 `Glass/PVK/Air`銆乣Glass/ITO/NiOx/SAM/PVK/Air` 涓庡畬鏁?stack 鐨勫眬閮ㄥ弽灏勭巼锛屽垽鏂?seam 鏄惁琚眰搴忔斁澶?
- 姣旇緝 `finite Ag + Air exit` 涓?`semi-infinite Ag`锛屽垽鏂?Ag 缁堢鏄惁鏄噸瑕佹斁澶у櫒
- 鏍告煡 Phase A-1 涓庡叏鏍堜富閾捐矾鏄惁瀛樺湪鎻掑€笺€佸眰搴忔垨杈圭晫鏉′欢 bug

杈撳嚭锛?
- `data/processed/phaseA1_seam_audit/pvk_seam_local_audit.csv`
- `data/processed/phaseA1_seam_audit/pvk_source_comparison.csv`
- `data/processed/phaseA1_seam_audit/seam_stack_sensitivity.csv`
- `data/processed/phaseA1_seam_audit/seam_ag_boundary_sensitivity.csv`
- `results/figures/phaseA1_seam_audit/*.png`
- `results/logs/phaseA1_seam_audit/phaseA1_seam_audit.md`

### 4.17 `stepA1_2_build_pvk_surrogate_v2.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepA1_2_build_pvk_surrogate_v2.py`
- 涓昏鑱岃矗锛氬熀浜?`digitized + extended + aligned v1 + seam audit` 缁撴灉锛岄噸寤?`PVK surrogate v2`锛屽湪鏉愭枡灞傝€屼笉鏄弽灏勭巼灞傛秷闄?`740-780 nm` 甯﹁竟 seam artifact

杈撳叆锛?
- `resources/aligned_full_stack_nk.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `data/processed/phaseA1_seam_audit/pvk_seam_local_audit.csv`
- `data/processed/phaseA1_seam_audit/pvk_source_comparison.csv`

鏍稿績澶勭悊娴佺▼锛?
- 瀵?`744-760 nm`銆乣740-770 nm`銆乣740-780 nm` 涓変釜鍊欓€?transition zone 鍋氬眬閮?surrogate 姣旇緝
- 鍦ㄨ繃娓″甫宸︿晶鐢?pre-seam `aligned v1` 閿氱偣鎷熷悎鍗曡皟 `PCHIP` 宸﹀弬鑰?
- 鍦ㄨ繃娓″甫鍐呭 `n` 浣跨敤 `smoothstep` 鏉冮噸妗ユ帴鍒?long-wave extended 瓒嬪娍
- 鍦ㄨ繃娓″甫鍐呭 `k` 浣跨敤 `smoothstep + cosine-tail decay`锛岄伩鍏?`750 nm` 璧风‖娓呴浂
- 浠?`螖R_stack(749->750)`銆乣螖R_total(749->750)`銆乣螖eps2`銆佸鏁?浜岄樁宸垎骞虫粦鎬у強 `810-1100 nm` fringe 淇濈湡搴﹁仈鍚堟墦鍒嗭紝閫夊嚭涓绘帹鑽愮増鏈?

杈撳嚭锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1_2/pvk_v2_candidate_metrics.csv`
- `data/processed/phaseA1_2/pvk_v1_v2_local_comparison.csv`
- `results/figures/phaseA1_2/pvk_v2_nk_local_zoom.png`
- `results/figures/phaseA1_2/pvk_v2_eps_local_zoom.png`
- `results/figures/phaseA1_2/pvk_v2_derivative_local_zoom.png`
- `results/figures/phaseA1_2/pvk_v1_vs_v2_overlay.png`
- `results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_build.md`

### 4.18 `stepA1_2_rerun_pristine_with_pvk_v2.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepA1_2_rerun_pristine_with_pvk_v2.py`
- 涓昏鑱岃矗锛氫繚鎸佸嚑浣曞拰鍏朵粬鏉愭枡瀹屽叏涓嶅彉锛屼粎鏇挎崲 PVK surrogate 涓?v2锛岄噸璺?pristine baseline 骞跺畬鎴?v1/v2 瀹氶噺瀵圭収

杈撳叆锛?
- `resources/aligned_full_stack_nk.csv`
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `data/processed/phaseA1_2/pvk_v2_candidate_metrics.csv`

鏍稿績澶勭悊娴佺▼锛?
- 澶嶇敤 `stepA1_pristine_baseline.py` 鐨勫父鏁扮幓鐠冧笌鍘氱幓鐠冮潪鐩稿共绾ц仈鍙ｅ緞
- 鐢熸垚 `R_front / R_stack / R_total` 鐨?v2 pristine baseline
- 姣旇緝 `749->750 nm` 鐨?seam 姝ラ暱銆乣740-780 nm` 鐨勫鏁?浜岄樁宸垎骞虫粦鎬э紝浠ュ強 `810-1100 nm` 鍚庣獥 fringe 淇濈湡搴?
- 杈撳嚭灞€閮?`720-780 nm` 瀵圭収鍥俱€佸叏璋?v1/v2 瀵圭収鍥句笌 Phase A-1.2 缁撹鏃ュ織

杈撳嚭锛?
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `results/figures/phaseA1_2/phaseA1_2_pristine_decomposition.png`
- `results/figures/phaseA1_2/phaseA1_2_pristine_3zones.png`
- `results/figures/phaseA1_2/phaseA1_2_pristine_720_780_zoom.png`
- `results/figures/phaseA1_2/phaseA1_2_pristine_v1_vs_v2_full_spectrum.png`
- `results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_rebuild.md`

### 4.19 `stepA2_pvk_thickness_scan.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepA2_pvk_thickness_scan.py`
- 涓昏鑱岃矗锛氬熀浜?`PVK surrogate v2` 鎵弿 `d_PVK` 瀵?pristine baseline 鐨勮皟鍒惰寰嬶紝寤虹珛鍘氬害-鏉＄汗鐩镐綅-璋卞舰鍥捐氨

杈撳叆锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `src/scripts/stepA1_pristine_baseline.py`

鏍稿績澶勭悊娴佺▼锛?
- 鍥哄畾 `Glass / ITO / NiOx / SAM / C60 / Ag` 涓庡父鏁扮幓鐠冨彛寰勶紝浠呮壂鎻?`d_PVK`
- 浠?`500-900 nm`銆乣5 nm` 姝ラ暱閲嶇畻 `R_stack / R_total`
- 鐩稿 `700 nm` 鍙傝€冨帤搴︽瀯閫?`螖R_stack` 涓?`螖R_total`
- 鍦?`810-1100 nm` 鍚庣獥鎻愬彇涓诲嘲銆佷富璋枫€佸嘲璋烽棿璺濅笌浠ｈ〃娉㈤暱鍙嶅皠鐜?
- 杈撳嚭 `R_stack / R_total / 螖R` 鐑姏鍥俱€乸eak/valley tracking 鍥惧拰浠ｈ〃鍘氬害鏇茬嚎鍥?

杈撳嚭锛?
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`
- `results/figures/phaseA2/phaseA2_R_stack_heatmap.png`
- `results/figures/phaseA2/phaseA2_R_total_heatmap.png`
- `results/figures/phaseA2/phaseA2_deltaR_stack_vs_700nm_heatmap.png`
- `results/figures/phaseA2/phaseA2_deltaR_total_vs_700nm_heatmap.png`
- `results/figures/phaseA2/phaseA2_peak_valley_tracking.png`
- `results/figures/phaseA2/phaseA2_selected_thickness_curves.png`
- `results/logs/phaseA2/phaseA2_pvk_thickness_scan.md`

### 4.20 `stepB1_rear_bema_sandbox.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepB1_rear_bema_sandbox.py`
- 涓昏鑱岃矗锛氬湪淇濇寔 `PVK surrogate v2` 涓庡悕涔夊嚑浣曚笉鍙樼殑鍓嶆彁涓嬶紝浠呭 `PVK/C60` 鍚庣晫闈㈠紩鍏?`50/50` solid-solid Bruggeman 绮楃硻灞傦紝寤虹珛 rear-only roughness 鎸囩汗瀛楀吀

杈撳叆锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`

鏍稿績澶勭悊娴佺▼锛?
- 鏋勫缓灞傚簭锛?
  - `Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK,C60) / C60_bulk / Ag / Air`
- 鍥哄畾 Bruggeman 浣撶Н鍒嗘暟涓?`50% PVK + 50% C60`
- 瀵?`d_BEMA,rear = 0-30 nm` 鍋?`1 nm` 鎵弿
- 鎵ц鍘氬害瀹堟亽锛?
  - `d_PVK,bulk = 700 - 0.5 * d_BEMA,rear`
  - `d_C60,bulk = max(0, 15 - 0.5 * d_BEMA,rear)`
- 璁＄畻 `R_stack / R_total / 螖R`锛屾彁鍙栧悗绐楀嘲璋枫€佸姣斿害鍜屾渶澶?`|螖R|`
- 涓?`Phase A-2` 鐨?`d_PVK` 鎸囩汗鍋氬悗绐?`螖R` 瀵圭収

杈撳嚭锛?
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_feature_summary.csv`
- `results/figures/phaseB1/phaseB1_R_stack_heatmap.png`
- `results/figures/phaseB1/phaseB1_R_total_heatmap.png`
- `results/figures/phaseB1/phaseB1_deltaR_stack_heatmap.png`
- `results/figures/phaseB1/phaseB1_deltaR_total_heatmap.png`
- `results/figures/phaseB1/phaseB1_selected_bema_curves.png`
- `results/figures/phaseB1/phaseB1_peak_valley_tracking.png`
- `results/figures/phaseB1/phaseB1_contrast_vs_bema.png`
- `results/figures/phaseB1/phaseB1_bema_vs_pvk_deltaR_comparison.png`
- `results/logs/phaseB1/phaseB1_rear_bema_sandbox.md`

### 4.21 `stepA2_1_pvk_uncertainty_ensemble.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepA2_1_pvk_uncertainty_ensemble.py`
- 涓昏鑱岃矗锛氬洿缁?`PVK surrogate v2` 鐨?`740-850 nm` band-edge / absorption-tail 涓嶇‘瀹氭€ф瀯寤哄皬鍨?ensemble锛屽苟鎶婅繖缁勫厛楠屾壈鍔ㄤ紶鎾埌 `d_PVK` 涓?rear-only BEMA 涓ょ被鏈哄埗

杈撳叆锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_feature_summary.csv`

鏍稿績澶勭悊娴佺▼锛?
- 浠?`PVK surrogate v2` 涓?nominal 鎴愬憳锛屾瀯寤猴細
  - `nominal`
  - `more_absorptive`
  - `less_absorptive`
- 鍦?`740-850 nm` 涓绘壈鍔ㄧ獥鍐呭 `k(位)` 鏂藉姞 smooth envelope 缂╂斁锛屽苟鐢ㄥ急鑰﹀悎 `n(位)` 淇淇濊瘉 `n/k/eps1/eps2` 杩炵画涓斿鏁板钩婊?
- 棰濆鍦?`730-900 nm` 杞獥鍐呮敹灏撅紝閬垮厤寮曞叆鏂扮殑 band-edge seam
- 杈撳嚭 ensemble 鐨?`n/k/eps/瀵兼暟` QA 鍥惧拰 local comparison 琛?
- 瀵逛唬琛ㄦ€у帤搴﹀瓙闆?`d_PVK = 600 / 700 / 800 nm` 閲嶇畻 `R_stack / R_total / 螖R`
- 瀵逛唬琛ㄦ€?rear-BEMA 瀛愰泦 `d_BEMA,rear = 0 / 10 / 20 / 30 nm` 閲嶇畻 `R_stack / R_total / 螖R`
- 璁＄畻 rear-window 涓?transition-window 鐨勭ǔ鍋ユ€ф憳瑕侊紝骞惰緭鍑?`robust vs surrogate-sensitive` 鐗瑰緛鐭╅樀

杈撳嚭锛?
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv`
- `data/processed/phaseA2_1/pvk_ensemble_manifest.csv`
- `data/processed/phaseA2_1/pvk_ensemble_local_comparison.csv`
- `data/processed/phaseA2_1/phaseA2_1_thickness_ensemble_scan.csv`
- `data/processed/phaseA2_1/phaseA2_1_thickness_robustness_summary.csv`
- `data/processed/phaseA2_1/phaseA2_1_rear_bema_ensemble_scan.csv`
- `data/processed/phaseA2_1/phaseA2_1_rear_bema_robustness_summary.csv`
- `data/processed/phaseA2_1/phaseA2_1_feature_robustness_matrix.csv`
- `results/figures/phaseA2_1/*.png`
- `results/logs/phaseA2_1/phaseA2_1_pvk_uncertainty_ensemble.md`

### 4.22 `stepB2_front_bema_sandbox.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepB2_front_bema_sandbox.py`
- 涓昏鑱岃矗锛氬湪鍥哄畾 `SAM` 鍘氬害鍜屽悕涔夊眰鍘氬彛寰勪笅锛屼娇鐢?`NiOx/PVK` 浣滀负鍓嶇晫闈?optical proxy锛屽缓绔?front-only BEMA 鎸囩汗瀛楀吀锛屽苟鍋氫唬琛ㄦ€?uncertainty spot-check

杈撳叆锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseA2_1/phaseA2_1_feature_robustness_matrix.csv`

鏍稿績澶勭悊娴佺▼锛?
- 鏋勫缓鍓嶇晫闈?proxy 灞傚簭锛?
  - `Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`
- 鍥哄畾 Bruggeman 浣撶Н鍒嗘暟涓?`50% NiOx + 50% PVK`
- 鍥哄畾 `SAM = 5 nm`銆乣NiOx = 45 nm`銆乣C60 = 15 nm`
- 瀵?`d_BEMA,front = 0-30 nm` 鍋?`1 nm` 鎵弿锛屽苟鎵ц瀹堟亽锛?
  - `d_PVK,bulk = 700 - d_BEMA,front`
- 杈撳嚭 `R_stack / R_total / 螖R` 鐑姏鍥俱€佸墠绐?杩囨浮鍖洪噸鐐瑰浘銆佷唬琛ㄦ洸绾裤€乸eak/valley tracking 涓庝笁鏈哄埗瀵圭収鍥?
- 瀵?`d_BEMA,front = 0 / 10 / 20 nm` 鍋?`nominal / more_absorptive / less_absorptive` spot-check锛屾彁鍙栫ǔ鍋ヤ笌鏁忔劅鐗瑰緛

杈撳嚭锛?
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_feature_summary.csv`
- `data/processed/phaseB2/phaseB2_front_bema_ensemble_spotcheck.csv`
- `data/processed/phaseB2/phaseB2_front_bema_robustness_summary.csv`
- `results/figures/phaseB2/*.png`
- `results/logs/phaseB2/phaseB2_front_bema_sandbox.md`

### 4.23 `stepC1a_rear_air_gap_sandbox.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepC1a_rear_air_gap_sandbox.py`
- 涓昏鑱岃矗锛氫粎鍦?`PVK/C60` 鍚庣晫闈㈠紩鍏ョ湡瀹?rear air gap锛屽缓绔?low-gap 楂樺垎杈ㄦ寚绾瑰瓧鍏革紝骞跺畬鎴?LOD 绮楄瘎浼颁笌 uncertainty spot-check

杈撳叆锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`

鏍稿績澶勭悊娴佺▼锛?
- 鏋勫缓灞傚簭锛?
  - `Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`
- rear-gap 琚涓虹湡瀹炲垎绂诲眰锛屼笉鍋氬帤搴﹀畧鎭掓墸鍑忥細
  - `d_PVK = 700 nm` fixed
  - `d_C60 = 15 nm` fixed
- 閲囩敤浣?gap 楂樺垎杈ㄦ壂鎻忥細
  - `0-20 nm`锛屾闀?`0.5 nm`
  - 棰濆琛?`25 / 30 / 40 / 50 nm`
- 杈撳嚭 `R_stack / R_total / 螖R` 鐑姏鍥俱€乼ransition/rear 鍝嶅簲鍥俱€乥ranch-aware peak/valley tracking銆佹尝鏁拌酱瀵圭収鍜屽洓鏈哄埗姣旇緝鍥?
- 瀵?`1 / 2 / 3 / 5 / 10 nm` 缁欏嚭鍩轰簬 `螖R_noise 鈮?0.2%` 鐨勭悊璁?LOD 绮楄瘎浼?
- 瀵?`0 / 2 / 5 / 10 nm` 鍋氫笁鎴愬憳 ensemble spot-check锛屽垽鏂摢浜涚粨璁虹ǔ鍋ャ€佸摢浜涚粷瀵归噺鏁忔劅

杈撳嚭锛?
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_feature_summary.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_lod_summary.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_ensemble_spotcheck.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_robustness_summary.csv`
- `results/figures/phaseC1a/*.png`
- `results/logs/phaseC1a/phaseC1a_rear_air_gap_sandbox.md`

### 4.24 `stepC1b_front_air_gap_sandbox.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepC1b_front_air_gap_sandbox.py`
- 涓昏鑱岃矗锛氫粎鍦?`SAM/PVK` 鍓嶇晫闈㈠紩鍏ョ湡瀹?front air-gap锛屽缓绔?low-gap 楂樺垎杈ㄦ寚绾瑰瓧鍏革紝骞跺畬鎴?LOD 绮楄瘎浼般€乽ncertainty spot-check 涓庝簲鏈哄埗瀵圭収

杈撳叆锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`

鏍稿績澶勭悊娴佺▼锛?
- 鏋勫缓灞傚簭锛?
  - `Glass / ITO / NiOx / SAM / Air_gap_front / PVK / C60 / Ag / Air`
- front-gap 琚涓虹湡瀹炲垎绂诲眰锛屼笉鍋氬帤搴﹀畧鎭掓墸鍑忥細
  - `d_SAM = 5 nm` fixed
  - `d_PVK = 700 nm` fixed
  - `d_C60 = 15 nm` fixed
- 閲囩敤浣?gap 楂樺垎杈ㄦ壂鎻忥細
  - `0-20 nm`锛屾闀?`0.5 nm`
  - 棰濆琛?`25 / 30 / 40 / 50 nm`
- 杈撳嚭 `R_stack / R_total / 螖R` 鐑姏鍥俱€乫ront/transition/rear 鍒嗙獥鍝嶅簲鍥俱€乺ear-window peak/valley tracking銆佹尝鏁拌酱瀵圭収鍜屼簲鏈哄埗姣旇緝鍥?
- 瀵?`1 / 2 / 3 / 5 / 10 nm` 缁欏嚭鍩轰簬 `螖R_noise 鈮?0.2%` 鐨勭悊璁?LOD 绮楄瘎浼?
- 瀵?`0 / 2 / 5 / 10 nm` 鍋氫笁鎴愬憳 ensemble spot-check锛屽垽鏂摢浜涚粨璁虹ǔ鍋ャ€佸摢浜涚粷瀵归噺鏁忔劅

杈撳嚭锛?
- `data/processed/phaseC1b/phaseC1b_front_air_gap_scan.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_feature_summary.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_lod_summary.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_ensemble_spotcheck.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_robustness_summary.csv`
- `results/figures/phaseC1b/*.png`
- `results/logs/phaseC1b/phaseC1b_front_air_gap_sandbox.md`

### 4.25 `stepPPT_phaseAtoC_assets.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepPPT_phaseAtoC_assets.py`
- 涓昏鑱岃矗锛氬熀浜?`Phase A-1.2` 鍒?`Phase C-1b` 鐨勬棦鏈?`processed/report` 缁撴灉锛岄噸缁樹竴濂楃粺涓€椋庢牸鐨?`R_total-only` PPT 姹囨姤璧勪骇锛屼笉寮曞叆浠讳綍鏂扮殑鐗╃悊妯℃嫙

杈撳叆锛?
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `data/processed/phaseA1_2/pvk_v1_v2_local_comparison.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_scan.csv`
- `results/report/phaseA*_*/PHASE_*.md`
- `results/report/phaseB*_*/PHASE_*.md`
- `results/report/phaseC*_*/PHASE_*.md`

鏍稿績澶勭悊娴佺▼锛?
- 缁熶竴閲嶇粯 baseline銆乼hickness銆乺ear-BEMA銆乫ront-BEMA銆乺ear-gap銆乫ront-gap 鐨?`R_total / Delta R_total` 涓诲浘
- 涓烘瘡涓€椤佃緭鍑?`main_figure.png / secondary_figure.png / slide_text.md / source_manifest.md`
- 鐢熸垚 `07_summary/mechanism_summary_matrix.png` 鍜?`appendix_pvk_surrogate_fix` 涓ゅ紶闄勫綍鍥?
- 鐢熸垚鎬?`00_manifest.md`锛岀敤浜庡揩閫熸嫾瑁?Phase A鈫扖 鐨?PPT 鍙欎簨绾?
- 鍚屾鏇存柊 `results/report/README.md` 涓?`report_manifest.csv`

杈撳嚭锛?
- `results/report/ppt_phaseAtoC_assets/00_manifest.md`
- `results/report/ppt_phaseAtoC_assets/01_baseline/*`
- `results/report/ppt_phaseAtoC_assets/02_thickness/*`
- `results/report/ppt_phaseAtoC_assets/03_rear_bema/*`
- `results/report/ppt_phaseAtoC_assets/04_front_bema/*`
- `results/report/ppt_phaseAtoC_assets/05_rear_gap/*`
- `results/report/ppt_phaseAtoC_assets/06_front_gap/*`
- `results/report/ppt_phaseAtoC_assets/07_summary/*`
- `results/report/ppt_phaseAtoC_assets/appendix_pvk_surrogate_fix/*`

### 4.26 `stepD1_airgap_discrimination_database.py`

- 鏂囦欢浣嶇疆锛歚src/scripts/stepD1_airgap_discrimination_database.py`
- 涓昏鑱岃矗锛氬湪 realistic `d_PVK + front/rear roughness` 鑳屾櫙涓婄粺涓€寤虹珛 `thickness nuisance / roughness nuisance / front-gap overlay / rear-gap overlay` 鐨?`R_total` 鍒ゅ埆鏁版嵁搴擄紝涓哄悗缁?air-gap 璇嗗埆绠楁硶姣旇緝鎻愪緵缁撴瀯鍖栬緭鍏?

杈撳叆锛?
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `results/report/phaseA2_pvk_thickness_scan/PHASE_A2_REPORT.md`
- `results/report/phaseA2_1_pvk_uncertainty_ensemble/PHASE_A2_1_REPORT.md`
- `results/report/phaseB1_rear_bema_sandbox/PHASE_B1_REPORT.md`
- `results/report/phaseB2_front_bema_sandbox/PHASE_B2_REPORT.md`
- `results/report/phaseC1a_rear_air_gap_sandbox/PHASE_C1A_REPORT.md`
- `results/report/phaseC1b_front_air_gap_sandbox/PHASE_C1B_REPORT.md`

鏍稿績澶勭悊娴佺▼锛?
- 澶嶇敤 `full_stack_microcavity.py` 鐨勭粍鍚堝叆鍙ｏ紝鍦ㄥ悓涓€ coherent stack 涓粺涓€鍔犲叆 `d_PVK`銆乫ront/rear BEMA background 涓庡崟渚?gap overlay
- 璁惧畾 realistic baseline锛歚d_PVK=700 nm, d_BEMA_front=10 nm, d_BEMA_rear=20 nm, no gap`
- 鏋勫缓浜旂被 logical family锛?
  - `thickness_nuisance`
  - `front_roughness_nuisance`
  - `rear_roughness_nuisance`
  - `front_gap_on_background`
  - `rear_gap_on_background`
- 棰濆淇濈暀 `background_anchor` 浣滀负 reference tracking family
- 瀵规瘡涓?logical case 杈撳嚭锛?
  - `R_total`
  - `Delta_R_total_vs_reference`
  - front / transition / rear 绐楀彛鐗瑰緛
  - rear-window shift matching
  - peak/valley 宸ョ▼鎽樿
- 杩涗竴姝ョ敓鎴?feature scatter / boxplots / discrimination atlas锛屽苟鍚屾鍐欏嚭 report 灞傝祫浜?

杈撳嚭锛?
- `data/processed/phaseD1/phaseD1_case_manifest.csv`
- `data/processed/phaseD1/phaseD1_rtotal_database.csv`
- `data/processed/phaseD1/phaseD1_feature_database.csv`
- `data/processed/phaseD1/phaseD1_discrimination_summary.csv`
- `results/figures/phaseD1/*.png`
- `results/logs/phaseD1/phaseD1_airgap_discrimination_database.md`
- `results/report/phaseD1_airgap_discrimination_database/`

## 5. Data Flow

褰撳墠椤圭洰涓绘暟鎹祦濡備笅锛?

```text
test_data/sample.csv
test_data/Ag-mirro.csv
resources/GCC-1022绯诲垪xlsx.xlsx
    -> step01_absolute_calibration.py
    -> data/processed/target_reflectance.csv

resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
    -> step01b_cauchy_extrapolation.py
    -> data/processed/CsFAPI_nk_extended.csv
    -> results/figures/cauchy_extrapolation_check.png

D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-150ms-{1,2,3}*.csv
D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-2000ms-{1,2,3}*.csv
D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-500us-1*.csv
D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-10ms-1*.csv
resources/GCC-1022绯诲垪xlsx.xlsx
    -> step06_single_sample_hdr_absolute_calibration.py
    -> src/core/hdr_absolute_calibration.py (鎵弿鏂囦欢 -> 璇诲彇 .spe 鏇濆厜鍏冩暟鎹?-> 鍚屾洕鍏夐噸澶嶆眰鍧囧€?-> Bit-Agnostic HDR 铻嶅悎 -> 閾堕暅鐞嗚鍙嶅皠鐜囨彃鍊?-> 缁濆鍙嶅皠鐜?QA)
    -> %TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_*.png
    -> %TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_curve_table.csv
    -> %TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_summary.md

D:\onedrive\Data\PL\2026\0409\cor\*-cor.csv
resources/GCC-1022绯诲垪xlsx.xlsx
    -> step06_batch_hdr_calibration.py
    -> src/core/hdr_absolute_calibration.py (鍏叡 Ag HDR 鍙傝€?-> 閫愭牱鏈?HDR 鎷兼帴 -> 缁濆鍙嶅皠鐜?-> 姹囨€诲彴璐?
    -> data/processed/phase06_batch/*_curve_table.csv
    -> data/processed/phase06_batch/phase06_batch_summary.csv
    -> results/figures/phase06_batch/*_QA_plot.png
    -> D:\onedrive\Data\PL\2026\0409\cor\hdr_results\*_hdr_curves.csv
    -> D:\onedrive\Data\PL\2026\0409\cor\hdr_results\*_hdr_qa.png
    -> D:\onedrive\Data\PL\2026\0409\cor\hdr_results\00_batch_summary_0409.csv

data/processed/target_reflectance.csv
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step02_tmm_inversion.py (CsFAPI 鎵╁睍 n-k -> ITO 鑹叉暎鍚告敹琛ュ伩 -> PVK 鑹叉暎鏂滅巼鎵板姩 -> NiOx 瀵勭敓鍚告敹 -> BEMA 绮楃硻灞備慨姝?-> 瀹忚鍘氬害楂樻柉骞冲潎 -> 鍏弬鏁板弽婕?
    -> results/figures/tmm_inversion_result.png

/Users/luxin/Library/CloudStorage/OneDrive-鍏变韩鐨勫簱-onedrive/Data/PL/2026/0403/cor/data-0403/*.csv
test_data/Ag-mirro.csv
resources/GCC-1022绯诲垪xlsx.xlsx
resources/ITO_20 Ohm_105 nm_e1e2.mat
data/processed/CsFAPI_nk_extended.csv
    -> step03_batch_fit_samples.py (缁濆鍙嶅皠鐜囨牎鍑?-> 鍏弬鏁伴€愭枃浠舵嫙鍚?-> 鍗曟牱鍝佸浘 / 鏇茬嚎 CSV / 姹囨€昏〃)
    -> results/figures/phase03_batch_fit/*.png
    -> data/processed/phase03_batch_fit/*.csv
    -> results/logs/phase03_batch_fit/*.csv
    -> OneDrive batch-fit-results/*

data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step03_forward_simulation.py (Phase 03 鍏弬鏁板熀绾垮浐鍖?-> 1050-1100 nm Cauchy 灏炬鎷熷悎 -> 1100-1500 nm PVK 灏鹃儴澶栨帹 -> Air_Gap 鎵弿 -> 螖R 闃堝€煎垽鍒?
    -> results/figures/phase04_air_gap_prediction.png

test_data/good-21.csv
test_data/bad-23.csv
test_data/Ag-mirro.csv
resources/GCC-1022绯诲垪xlsx.xlsx
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step04a_air_gap_diagnostic.py (浠ｈ〃璋辩粷瀵规爣瀹?-> good 鍏弬鏁板弬鑰冩嫙鍚?-> bad 鍏弬鏁板熀绾挎嫙鍚?-> SAM/PVK 绌烘皵闅欎竷鍙傛暟璇婃柇鎷熷悎 -> 螖R 鎸囩汗姣斿)
    -> data/processed/phase04a/*_calibrated.csv
    -> results/figures/phase04a_air_gap_diagnostic.png
    -> results/logs/phase04a_air_gap_diagnostic.md

test_data/good-21.csv
test_data/bad-20-2.csv
test_data/Ag-mirro.csv
resources/GCC-1022绯诲垪xlsx.xlsx
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step04b_air_gap_localization.py (浠ｈ〃璋辩粷瀵规爣瀹?-> good 鍏弬鏁板熀鍑嗘彁鍙?-> L1/L2/L3 绌烘皵闅欑┖闂村畾浣?-> 鏈€浼樹綅缃潗鏂欏弬鏁板紱璞?
    -> data/processed/phase04b/*_calibrated.csv
    -> results/figures/phase04b_localization.png
    -> results/logs/phase04b_localization.md

data/processed/target_reflectance.csv
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> diagnostics_shape_mismatch.py
    -> results/figures/diagnostic_shape_analysis.png
    -> results/logs/phase02_shape_diagnostic_report.md

reference/Khan.../images/b3c499f799...
    -> step02_digitize_fapi_optical_constants.py
    -> resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv

reference/Khan.../images/4ad6d508...
reference/Khan.../images/885e29d3...
    -> step02_digitize_csfapi_optical_constants.py
    -> resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv

resources/n-kdata/*/full.md
    -> step05_parse_ellipsometry_markdown.py
    -> resources/materials_master_db.json

resources/n-kdata/*.pdf
resources/materials_master_db.json
    -> step05b_verify_against_pdf.py
    -> resources/materials_master_db.json

resources/materials_master_db.json
resources/ITO-NK鍊?csv
resources/NIOX-NK鍊?csv
resources/C60nk鍊?csv
resources/SNO-NK鍊?csv
data/processed/CsFAPI_nk_extended.csv
resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
resources/Ag.csv
    -> step05c_build_aligned_nk_stack.py
    -> resources/aligned_full_stack_nk.csv

resources/aligned_full_stack_nk.csv
resources/materials_master_db.json
    -> step06_dual_mode_microcavity_sandbox.py (鍏ㄥ櫒浠惰琛?-> Baseline/Case A/Case B 鍫嗘爤鏋勫缓 -> d_air 鎵弿 -> 鍙屾ā寮?螖R 瀛楀吀 / 瀵规瘮鍥?/ 闆疯揪鍥?
    -> data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv
    -> results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png
    -> results/figures/phase06_dual_mode_radar_map.png
    -> results/logs/phase06_dual_mode_microcavity_sandbox.md

resources/aligned_full_stack_nk.csv
resources/materials_master_db.json
    -> step07_orthogonal_radar_and_baseline.py (LM 鍙嬪ソ鍓嶅悜鎺ュ彛 -> pristine 鍏ㄨ氨鍩哄噯鍥?-> front/back 姝ｄ氦闆疯揪 -> 鍒嗗尯璇婃柇)
    -> data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv
    -> results/figures/phase07_baseline_3zones.png
    -> results/figures/phase07_orthogonal_radar.png
    -> results/logs/phase07_orthogonal_radar_diagnostic.md

test_data/phase7_data/*_hdr_curves.csv
or test_data/phase7_data/*-cor.csv + *.spe
resources/GCC-1022绯诲垪xlsx.xlsx
resources/aligned_full_stack_nk.csv
    -> step07_dual_window_inversion.py (鍘熷澶氭洕鍏?HDR 涓棿浠跺弻鍏ュ彛 -> 鏍囧噯鍖?fit_input -> 鍙岀獥鍔犳潈 TMM -> basin 鎵弿 -> DE + least-squares -> 鍥捐〃 / 鏃ュ織 / 鍙拌处)
    -> data/processed/phase07/phase07_source_manifest.csv
    -> data/processed/phase07/phase07_fit_summary.csv
    -> data/processed/phase07/fit_inputs/*_fit_input.csv
    -> data/processed/phase07/fit_results/*_fit_curve.csv
    -> data/processed/phase07/fit_results/*_fit_summary.csv
    -> results/figures/phase07/*_full_spectrum.png
    -> results/figures/phase07/*_dual_window_zoom.png
    -> results/figures/phase07/*_residual_diagnostics.png
    -> results/figures/phase07/*_rear_basin_scan.png
    -> results/logs/phase07/*_optimizer_log.md

data/processed/phase07/phase07_fit_summary.csv
data/processed/phase07/fit_inputs/*_fit_input.csv
resources/aligned_full_stack_nk.csv
    -> step08_theoretical_tmm_modeling.py (鍐荤粨 Phase 07 鍙傛暟 -> 閲嶅缓鐗╃悊鍙嶅皠鐜?-> 鍓嶈〃闈㈡暎灏勬槧灏?-> 鍚庣獥 z-score 鐞嗚鏍稿 -> 鎵归噺杈撳嚭)
    -> data/processed/phase08/phase08_theory_summary.csv
    -> data/processed/phase08/phase08_source_manifest.csv
    -> data/processed/phase08/theory_curves/*_theory_curve.csv
    -> results/figures/phase08/*_theory_vs_measured.png
    -> results/logs/phase08/phase08_theoretical_tmm_modeling.md

resources/aligned_full_stack_nk.csv
    -> stepA1_pristine_baseline.py (甯告暟鐜荤拑瑕嗙洊 -> Fresnel 鍓嶈〃闈?-> 鍚庝晶鐩稿共 stack -> 鍘氱幓鐠冮潪鐩稿共绾ц仈 -> 鍒嗚В鍥?/ 涓夊尯鍥?/ 鏃ュ織)
    -> data/processed/phaseA1/phaseA1_pristine_baseline.csv
    -> results/figures/phaseA1/phaseA1_pristine_decomposition.png
    -> results/figures/phaseA1/phaseA1_pristine_3zones.png
    -> results/logs/phaseA1/phaseA1_pristine_baseline.md

resources/aligned_full_stack_nk.csv
data/processed/phaseA1/phaseA1_pristine_baseline.csv
data/processed/CsFAPI_nk_extended.csv
resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
src/scripts/step05c_build_aligned_nk_stack.py
    -> stepA1_1_pvk_seam_audit.py (PVK seam 灞€閮ㄦ硶鍖诲璁?-> 涓夋簮杩芥函 -> 鍫嗘爤鏀惧ぇ姣旇緝 -> Ag 杈圭晫瀵圭収 -> 浠ｇ爜绾ф帓鏌?
    -> data/processed/phaseA1_seam_audit/*.csv
    -> results/figures/phaseA1_seam_audit/*.png
    -> results/logs/phaseA1_seam_audit/phaseA1_seam_audit.md

resources/aligned_full_stack_nk.csv
data/processed/CsFAPI_nk_extended.csv
resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
data/processed/phaseA1_seam_audit/*.csv
    -> stepA1_2_build_pvk_surrogate_v2.py (鍊欓€?transition zone 鎵弿 -> smoothstep n bridge + cosine-tail k decay -> seam 鎸囨爣 / 骞虫粦鎬?/ fringe 淇濈湡搴﹁仈鍚堟墦鍒?
    -> resources/aligned_full_stack_nk_pvk_v2.csv
    -> data/processed/phaseA1_2/pvk_v2_candidate_metrics.csv
    -> data/processed/phaseA1_2/pvk_v1_v2_local_comparison.csv
    -> results/figures/phaseA1_2/pvk_v2_*.png
    -> results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_build.md

resources/aligned_full_stack_nk_pvk_v2.csv
data/processed/phaseA1/phaseA1_pristine_baseline.csv
    -> stepA1_2_rerun_pristine_with_pvk_v2.py (浠呮浛鎹?PVK surrogate -> pristine baseline rerun -> seam 姝ラ暱 / 灞€閮ㄥ钩婊戞€?/ 鍚庣獥 fringe 淇濈湡搴﹀鐓?
    -> data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv
    -> results/figures/phaseA1_2/phaseA1_2_pristine_*.png
    -> results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_rebuild.md

resources/aligned_full_stack_nk_pvk_v2.csv
    -> stepA2_pvk_thickness_scan.py (鎵弿 d_PVK -> pristine baseline rerun -> rear-window peak/valley tracking -> R/螖R 鐑姏鍥?
    -> data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
    -> data/processed/phaseA2/phaseA2_pvk_feature_summary.csv
    -> results/figures/phaseA2/phaseA2_*.png
    -> results/logs/phaseA2/phaseA2_pvk_thickness_scan.md

resources/aligned_full_stack_nk_pvk_v2.csv
data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
    -> stepB1_rear_bema_sandbox.py (rear-only PVK/C60 BEMA -> 鍘氬害瀹堟亽 -> R/螖R 鐑姏鍥?-> d_PVK 姝ｄ氦瀵圭収)
    -> data/processed/phaseB1/phaseB1_rear_bema_scan.csv
    -> data/processed/phaseB1/phaseB1_rear_bema_feature_summary.csv
    -> results/figures/phaseB1/phaseB1_*.png
    -> results/logs/phaseB1/phaseB1_rear_bema_sandbox.md

resources/aligned_full_stack_nk_pvk_v2.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB1/phaseB1_rear_bema_scan.csv
    -> stepA2_1_pvk_uncertainty_ensemble.py (PVK nominal/more/less absorptive ensemble -> thickness 瀛愰泦浼犳挱 -> rear-BEMA 瀛愰泦浼犳挱 -> robustness summary / feature matrix)
    -> resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
    -> data/processed/phaseA2_1/*.csv
    -> results/figures/phaseA2_1/*.png
    -> results/logs/phaseA2_1/phaseA2_1_pvk_uncertainty_ensemble.md

resources/aligned_full_stack_nk_pvk_v2.csv
resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB1/phaseB1_rear_bema_scan.csv
    -> stepB2_front_bema_sandbox.py (front-only NiOx/PVK proxy BEMA -> PVK 瀹堟亽鎵ｅ噺 -> R/螖R 鐑姏鍥?-> front/rear/thickness 瀵圭収 -> lightweight uncertainty spot-check)
    -> data/processed/phaseB2/*.csv
    -> results/figures/phaseB2/*.png
    -> results/logs/phaseB2/phaseB2_front_bema_sandbox.md

resources/aligned_full_stack_nk_pvk_v2.csv
resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB1/phaseB1_rear_bema_scan.csv
data/processed/phaseB2/phaseB2_front_bema_scan.csv
    -> stepC1a_rear_air_gap_sandbox.py (rear air-gap only -> low-gap high-resolution scan -> branch-aware tracking -> LOD绮楄瘎浼?-> thickness/rear-BEMA/front-BEMA 鍥涙満鍒跺鐓?-> uncertainty spot-check)
    -> data/processed/phaseC1a/*.csv
    -> results/figures/phaseC1a/*.png
    -> results/logs/phaseC1a/phaseC1a_rear_air_gap_sandbox.md

resources/aligned_full_stack_nk_pvk_v2.csv
resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB2/phaseB2_front_bema_scan.csv
data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv
    -> stepC1b_front_air_gap_sandbox.py (front air-gap only -> low-gap high-resolution scan -> front/transition/rear 鍒嗙獥鍝嶅簲 -> LOD绮楄瘎浼?-> thickness/front-BEMA/rear-gap 浜旀満鍒跺鐓?-> uncertainty spot-check)
    -> data/processed/phaseC1b/*.csv
    -> results/figures/phaseC1b/*.png
    -> results/logs/phaseC1b/phaseC1b_front_air_gap_sandbox.md

selected phase outputs
    -> results/report/ (绮鹃€?CSV / PNG / Markdown 姹囨姤灞?
    -> results/report/phaseA1_2_pvk_surrogate_and_pristine/*
    -> results/report/phaseA2_1_pvk_uncertainty_ensemble/*
    -> results/report/phaseA2_pvk_thickness_scan/*
    -> results/report/phaseB1_rear_bema_sandbox/*
    -> results/report/phaseB2_front_bema_sandbox/*
    -> results/report/phaseC1a_rear_air_gap_sandbox/*
    -> results/report/phaseC1b_front_air_gap_sandbox/*
    -> results/report/ppt_phaseAtoC_assets/*
```

鍙寜 SOP 鐞嗚В涓猴細

1. `step01` 璐熻矗鎶婂師濮嬭鏁版牎鍑嗘垚鍙敤浜庣墿鐞嗗缓妯＄殑缁濆鍙嶅皠鐜?
2. `step01b` 鎶?[LIT-0001] 鏁板瓧鍖?CsFAPI 鏇茬嚎杞崲鎴愭爣鍑嗚繎绾㈠ `n-k` 涓棿浠?
3. `step02` 鍦ㄦ秷璐规爣鍑?`n-k` 涓棿浠跺悗锛屽厛瀵?ITO 鐨勬秷鍏夌郴鏁?`k` 鍋氶敋瀹?`850-1100 nm` 鐨勮壊鏁ｅ惛鏀惰ˉ鍋匡紝鍐嶅 PVK 鏂滅巼鍜?NiOx 鍚告敹鍋氬井璋冿紝閫氳繃 50/50 BEMA 灏?PVK-Air 琛ㄩ潰绮楃硻搴︽姌绠椾负鏈夋晥浠嬭川灞傦紝骞跺 `d_bulk` 鍋氶珮鏂帤搴﹀钩鍧?
4. `step03_forward_simulation.py` 缁ф壙涓婅堪鍩虹嚎锛屽苟閫氳繃 `Air_Gap` 缂洪櫡灞傛妸鍙嶆紨寮曟搸鎵╁睍涓衡€滃墠鍚戦娴嬮浄杈锯€濓紝鐩存帴杈撳嚭闅愭€у墺绂诲湪 `850-1500 nm` 鐨?`R / 螖R` 鍙娴嬫€у浘
5. `step04a_air_gap_diagnostic.py` 杩涗竴姝ユ妸浠ｈ〃鎬у師濮嬭氨鎷夊洖鍒板崟鏍峰搧璇婃柇闂幆锛岀敤 `good-21` 浣滀负鍙傝€冩牱鏈€佸湪 `bad-23` 涓婃樉寮忔楠?`SAM/PVK` 绌烘皵闅欏亣璁?
6. `step04b_air_gap_localization.py` 鍒欒繘涓€姝ユ妸鍋囪浠庘€滄槸鍚︽湁绌烘皵闅欌€濇帹杩涘埌鈥滅┖姘旈殭鏈€鍙兘浣嶄簬鍝釜鐣岄潰锛屼互鍙婃潗鏂欏弬鏁版槸鍚︿篃蹇呴』鍙戠敓婕傜Щ鈥?
7. `step05` / `step05b` / `step05c` 杩涗竴姝ユ妸鏉愭枡鎶ュ憡瑙ｆ瀽銆丳DF 鏍￠獙鍜屽叏鏍?`n-k` 瀵归綈琛ㄥ缓绔嬩负闀挎湡鍙鐢ㄧ殑鏁版嵁灞?
8. `step06_dual_mode_microcavity_sandbox.py` 鍒欏湪涓嶅啀寮曞叆鎷熷悎鑷敱搴︾殑鍓嶆彁涓嬶紝鎶婂叏鏍堟潗鏂欒〃鐩存帴杞负鍙屾ā寮忓井鑵旂己闄峰瓧鍏革紝鐢ㄤ簬鍚庣画缂洪櫡瀹氶噺鍜屾寚绾瑰尮閰?
9. `step07_orthogonal_radar_and_baseline.py` 杩涗竴姝ユ妸缂洪櫡妯″紡鍘嬬缉涓?`front/back` 涓ょ被瀹忚姝ｄ氦鐣岄潰锛屽苟琛ヤ笂闈㈠悜鍚庣画 LM 鐨勬爣鍑嗗墠鍚戞帴鍙ｄ笌涓夊垎鍖哄熀鍑嗗彲瑙嗗寲
10. `step07_dual_window_inversion.py` 鍒欐妸 `Phase 06 HDR`銆乣Phase 05c 瀵归綈 n-k` 鍜?`Phase 07 鍙岀獥鍙嶆紨` 鎺ユ垚褰撳墠涓诲共闂幆锛岃兘澶熺洿鎺ユ妸 `hdr_curves` 鏍锋湰杞负鏍囧噯鍖栨嫙鍚堣緭鍏ャ€佸弬鏁拌〃銆侀€愭尝闀挎嫙鍚堣〃銆佷紭鍖栨棩蹇楀拰璇婃柇鍥?
11. `step08_theoretical_tmm_modeling.py` 鍦ㄤ笉鏂板鎷熷悎鑷敱搴︾殑鍓嶆彁涓嬶紝鎶?`Phase 07` 鐨勬渶浼樺弬鏁板浐鍖栦负鍙鐜扮殑鍓嶅悜寤烘ā杈撳嚭锛屼究浜庡悗缁仛缁撴瀯鍋囪瀵规瘮鍜岃法鏍锋湰鐞嗚瀹¤
12. `stepA1_pristine_baseline.py` 鍒欒繘涓€姝ユ妸鍏ㄦ爤鏉愭枡琛ㄥ帇缂╀负鏈€涓ユ牸鐨勯浂缂洪櫡鍙傝€冭氨锛屾樉寮忔媶寮€ `R_front`銆乣R_stack` 涓?`R_total`
13. `stepA1_1_pvk_seam_audit.py` 鍒欐妸 Phase A-1 涓毚闇茬殑 `749/750 nm` 鍙伴樁杩芥函鍒?PVK seam锛屾湰璐ㄤ笂涓哄悗缁?repair 鎻愪緵璇佹嵁閾捐€屼笉鏄洿鎺ヤ慨澶?
14. `stepA1_2_build_pvk_surrogate_v2.py` 鍦ㄦ潗鏂欏眰閲嶅缓 `PVK surrogate v2`锛屾妸 `749/750 nm` 鐨勮烦鐐归檷绾т负杩炵画 band-edge 杩囨浮
15. `stepA1_2_rerun_pristine_with_pvk_v2.py` 杩涗竴姝ラ獙璇佷慨澶嶅悗 `螖R_stack(749->750)` 涓?`螖R_total(749->750)` 宸叉樉钁楀帇浣庯紝鍚屾椂鍚庣獥 fringe 淇濇寔绋冲畾
16. `stepA2_pvk_thickness_scan.py` 杩涗竴姝ユ妸 repaired pristine baseline 鎺ㄨ繘涓哄帤搴?鏉＄汗鐩镐綅鍥捐氨锛屽彲鐩存帴鍖哄垎鈥滃帤搴﹀鑷寸殑鍏ㄥ眬 fringe 婕傜Щ鈥濅笌鈥滅晫闈㈢己闄峰鑷寸殑灞€閮ㄦ壈鍔ㄢ€?
17. `stepB1_rear_bema_sandbox.py` 鍒欐妸 rear-only `PVK/C60` intermixing 鍗曠嫭鎷嗘垚鐙珛鏈哄埗锛屽緱鍒颁笌 `d_PVK` 鍙瘮杈冪殑鍚庣晫闈㈢矖绯欐寚绾?
18. `stepA2_1_pvk_uncertainty_ensemble.py` 鍒欐妸 `PVK surrogate v2` 鐨?band-edge 涓嶇‘瀹氭€ф寮忎紶鎾埌 thickness 涓?rear-BEMA 涓ょ被鏈哄埗锛岀敤浜庡尯鍒嗛珮缃俊搴︾粨鏋勬寚绾瑰拰 surrogate-sensitive 鐗瑰緛
19. `stepB2_front_bema_sandbox.py` 鍒欐妸鍓嶇晫闈?`NiOx/PVK` optical proxy 鍗曠嫭鎷嗘垚绗笁绫绘満鍒讹紝褰㈡垚涓?thickness / rear-BEMA 骞跺垪鐨?front-side roughness 鎸囩汗
20. `stepC1a_rear_air_gap_sandbox.py` 鍒欐妸鐪熷疄 rear air-gap 浣滀负绗洓绫绘満鍒跺崟鐙紩鍏ワ紝鎻愪緵涓?thickness / front-BEMA / rear-BEMA 鍙洿鎺ユ瘮杈冪殑鍒嗙灞傛寚绾逛笌鐞嗚 LOD
21. 褰撳墠鑴氭湰閾惧凡缁忓叿澶団€滄枃鐚暟瀛楀寲 / 妞亸鎶ュ憡瑙ｆ瀽 -> 鏉愭枡鏁版嵁搴?-> 鍏ㄦ爤瀵归綈 `n-k` 琛?-> pristine baseline decomposition -> seam forensic audit -> surrogate rebuild -> pristine rerun -> thickness scan -> rear-only BEMA sandbox -> PVK uncertainty propagation -> front-only BEMA sandbox -> rear air-gap sandbox -> 瀹忚姝ｄ氦鐣岄潰鎸囩汗瀛楀吀 -> 鍙岀獥鑱斿悎鍙嶆紨 -> 鍥哄畾鍙傛暟鐞嗚閲嶅缓鈥濈殑鍓嶅悜-鍙嶆紨鑱斿悎鍩虹嚎

## 6. Key Physical / Numerical Assumptions

褰撳墠瀹炵幇涓渶閲嶈鐨勭墿鐞嗗拰鏁板€煎亣璁惧涓嬶細

- `step02` 鍙嶆紨绐楀彛涓?`850-1100 nm`锛宍step03_forward_simulation.py` 鐨勫墠鍚戦娴嬬獥鍙ｆ墿灞曞埌 `850-1500 nm`
- `step04a_air_gap_diagnostic.py` 鍦?`850-1100 nm` 鐨勫疄楠岄噰鏍风綉鏍间笂姣旇緝 `good-21` 涓?`bad-23`锛屼笉閲嶉噰鏍峰埌鍧囧寑 1 nm 缃戞牸
- 鐜荤拑鍘氭澘涓嶄綔涓虹浉骞插眰鐩存帴杩涘叆 TMM 鐩镐綅鐭╅樀
- ITO 鏁版嵁鑻ユ尝闀块噺绾уぇ浜?`2000`锛屽垯鎸?Angstrom 鑷姩杞负 nm
- 鍘傚閾堕暅鍩哄噯鑻ユ暟鍊艰寖鍥村ぇ浜?`1.5`锛屽垯鎸夌櫨鍒嗘瘮杞负 `0-1` 灏忔暟
- PVK 鐨勮繎绾㈠鑹叉暎鏉ユ簮涓?[LIT-0001] Fig. 3 鐨?`ITO/CsFAPI` 鏁板瓧鍖?`n` 鏇茬嚎锛屽苟閫氳繃 Cauchy 妯″瀷澶栨帹鍒?`1100 nm`
- `750-1100 nm` 鍐呭己鍒堕噰鐢?`k = 0`
- Phase A-1.2 鏂板 `PVK surrogate v2`锛?
  - 浠呭 `740-780 nm` band-edge 鍖哄煙鍋氬眬閮?surrogate rebuild
  - 涓绘帹鑽?transition zone 涓?`740-780 nm`
  - `n` 鐢?`smoothstep` 妗ユ帴鍒?long-wave 瓒嬪娍锛宍k` 鐢?`smoothstep + cosine-tail` 琛板噺鍒伴€忔槑灏?
  - 涓嶅啀鍏佽 `750 nm` 璧?`k = 0` 鐨勭‖鍒囨崲
- Phase A-2 鍥哄畾 `PVK surrogate v2` 涓庡叾浣欐潗鏂欏弬鏁帮紝浠呮壂鎻?`d_PVK`锛屽洜姝ゅ綋鍓嶅帤搴︾伒鏁忓害鍥捐氨鍙嶆槧鐨勬槸鈥滈浂缂洪櫡寰厰鍏夌▼鍙樺寲鈥濓紝涓嶆槸缂洪櫡璋冨埗鍙犲姞缁撴灉
- Phase B-1 鍥哄畾 `PVK surrogate v2` 涓庡悕涔夊眰鍘氾紝浠呭湪 `PVK/C60` 鍚庣晫闈㈠姞鍏?`50/50` solid-solid BEMA锛屽苟鎵ц `PVK/C60` 瀹堟亽鎵ｅ噺锛屽洜姝ゅ綋鍓?rear-BEMA 鎸囩汗鍙嶆槧鐨勬槸鈥滃悗鐣岄潰 intermixing + 鐩搁偦灞傚彉钖勨€濈殑鑱斿悎鏈哄埗
- Phase A-2.1 杩涗竴姝ュ紩鍏ヤ笁鎴愬憳 PVK uncertainty ensemble锛?
  - `nominal` 鐩存帴娌跨敤 `PVK surrogate v2`
  - `more_absorptive` 鍦?`740-850 nm` 澧炲己 `k(位)` 鍚告敹灏撅紝骞跺仛寮辫€﹀悎 `n(位)` 涓婅皟
  - `less_absorptive` 鍦?`740-850 nm` 鍓婂急 `k(位)` 鍚告敹灏撅紝骞跺仛寮辫€﹀悎 `n(位)` 涓嬭皟
  - 涓夋垚鍛橀兘瑕佹眰鍦?`730-900 nm` 淇濇寔杩炵画銆佹棤鏂?seam锛屼笖涓嶇牬鍧?`850-1100 nm` 鐨?nominal rear-window 瓒嬪娍
- 褰撳墠 A-2.1 鐨?first-pass 浼犳挱缁撴灉琛ㄦ槑锛?
  - `d_PVK` 鐨?rear-window 鐩镐綅/宄颁綅婕傜Щ缁撹瀵?surrogate 閫夋嫨楂樺害绋冲仴
  - rear-only BEMA 鐨勨€滃眬閮ㄥ寘缁?杞诲井鎸箙鎵板姩鈥濈粨璁轰粛鎴愮珛锛屼絾鍏跺箙鍊奸噺绾у band-edge 鍏堥獙鏁忔劅
  - 缁濆 `R_total(780 nm)` 涓€绫?band-edge 閭诲煙瑙傛祴閲忎笉瀹滅洿鎺ヤ綔涓洪珮缃俊搴︾粨鏋勫綊鍥犵壒寰?
- Phase B-2 杩涗竴姝ュ紩鍏?front-only `NiOx/PVK` proxy BEMA锛?
  - 灞傚簭鍥哄畾涓?`Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`
  - `SAM`銆乣NiOx` 涓?`C60` 鍘氬害鍥哄畾涓嶅彉
  - 瀹堟亽浠呬綔鐢ㄤ簬 `PVK`锛歚d_PVK,bulk = 700 - d_BEMA,front`
  - 褰撳墠缁撴灉琛ㄦ槑 front-BEMA 鐨勪富鍝嶅簲鍋忓悜 `400-810 nm` 鐨勫墠绐?杩囨浮鍖猴紝鑰屼笉鏄?rear-window 涓荤浉浣嶆満鍒?
- Phase B-2 鐨?spot-check 杩涗竴姝ヨ〃鏄庯細
  - front-window 骞冲潎 `螖R` 灞炰簬杈冪ǔ鍋ョ壒寰?
  - transition/rear 鎸箙閲忕骇涓?`R_total(780 nm)` 浠嶄細鍙楀埌 surrogate 鍏堥獙褰卞搷
- Phase C-1a 杩涗竴姝ュ紩鍏?rear air-gap only锛?
  - 灞傚簭鍥哄畾涓?`Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`
  - rear-gap 琚涓虹湡瀹炲垎绂诲眰锛屼笉鍋?`PVK/C60` 鍘氬害瀹堟亽鎵ｅ噺
  - 浣?gap 鍖哄煙閲囩敤 `0-20 nm / 0.5 nm` 楂樺垎杈ㄦ壂鎻忥紝骞惰ˉ `25 / 30 / 40 / 50 nm`
- 褰撳墠 C-1a 鐨?first-pass 缁撴灉琛ㄦ槑锛?
  - rear-gap 鐨勪富鏁忔劅绐楀彛浣嶄簬 transition/rear锛岀悊璁?LOD 鍦?`1 nm` 绾у凡缁忚秴杩?`0.2%`
  - rear-gap 姣?rear-BEMA 鏇村己銆佹洿闈炵嚎鎬э紝涔熸瘮 thickness 鏇翠笉鍍忓叏灞€骞崇Щ
  - rear-gap 鍙綔涓轰笌 thickness / rear-BEMA / front-BEMA 骞跺垪鐨勭鍥涚被鏈哄埗瀛楀吀
- `1000-1100 nm` 灞炰簬瓒呭嚭鍘熷妞亸娴嬮噺绐楀彛鐨勬ā鍨嬪鎺ㄥ尯
- Phase 04 涓?`1100-1500 nm` 鐨?PVK 鎶樺皠鐜囦笉鍐嶇洿鎺ユ部鐢ㄨ〃鏍硷紝鑰屾槸鍩轰簬 `1050-1100 nm` 鐨勭湡瀹炵偣浜屾鎷熷悎 Cauchy 灏炬鍚庣户缁鎺紝涓斾粛寮哄埗 `k = 0`
- 绮楃硻灞傞噰鐢?`50% PVK + 50% Air` 鐨?BEMA 鏈夋晥浠嬭川
- ITO 鐨勯澶栧惛鏀朵互閿佸畾瀹為儴 `n` 鐨勮壊鏁ｅ弬鏁?`ito_alpha` 琛ㄧず锛屽叾瀵?`k` 鐨勬斁澶у湪 `850 nm` 澶勪负 1锛屽湪 `1100 nm` 澶勪负 `1 + ito_alpha`
- Phase 04 涓 ITO 闀挎尝鍚告敹琛ュ伩鍦?`1100 nm` 鍚庝繚鎸侀ケ鍜岋紝涓嶇户缁悜 `1500 nm` 澧為暱
- 鍙嶆紨褰撳墠鍚屾椂鎷熷悎 `d_bulk`銆乣d_rough`銆乣ito_alpha`銆乣sigma_thickness`銆乣pvk_b_scale` 涓?`niox_k` 鍏釜鍙傛暟
- Phase 04a 鐨勭┖姘旈殭鍋囪浣嶇疆鏄惧紡鍥哄畾涓?`SAM / PVK` 鐣岄潰锛屽嵆灞傚簭 `Glass -> ITO -> NiOx -> SAM -> Air_Gap -> PVK_Bulk -> PVK_Roughness -> Air`
- Phase 04a 鐨?7 鍙傛暟璇婃柇涓紝`ito_alpha`銆乣pvk_b_scale` 涓?`niox_k` 閿佸畾涓?`good-21` 鍏弬鏁版渶浣虫嫙鍚堝€硷紝鍙斁寮€ `d_bulk`銆乣d_rough`銆乣sigma_thickness` 涓?`d_air`
- Phase 04b 鐨勭┖闂村畾浣嶉樁娈靛垎鍒祴璇?`Glass/ITO`銆乣ITO/NiOx` 涓?`SAM/PVK` 涓変釜鍊欓€夌┖姘旈殭鐣岄潰
- Phase 04b 鐨勬潗鏂欏紱璞樁娈靛厑璁?`ito_alpha`銆乣pvk_b_scale` 涓?`niox_k` 鍦?`good-21` 鍩哄噯鍊肩殑 `卤15%` 鑼冨洿鍐呮紓绉?
- Phase 07 鐨勬嫙鍚堢獥鍙ｅ浐瀹氫负锛?
  - `500-650 nm` 鍓嶇獥
  - `650-860 nm` 灞忚斀鍖?
  - `860-1055 nm` 鍚庣獥
- Phase 07 鐨勭矖绯欏眰宸叉敼涓?`50% PVK + 50% C60` 鐨?BEMA锛岃€岄潪鏃?Phase 鐨?`PVK + Air`
- Phase 07 寮哄埗鎵ц C60 瀹堟亽锛?
  - `d_C60_bulk = max(0, 15 - 0.5 * d_rough)`
- Phase 07 涓?`d_rough` 鐨勭墿鐞嗕笂闄愬浐瀹氫负 `30 nm`
- Phase 07 鐨勭獥鍙ｅ綊涓€鍖栧昂搴﹂噰鐢細
  - `scale_w = max(median(R_meas_w), 1.4826 * MAD(R_meas_w), 0.005)`
- Phase 07 鐨勫帤鐜荤拑鎬诲弽灏勭巼閲囩敤锛?
  - `R_total = R_front + (T_front^2 * R_stack) / (1 - R_front * R_stack)`
- Phase 07 鐨勪紭鍖栫瓥鐣ヤ负锛?
  - `d_bulk` 鍚庣獥 basin 鎵弿
  - basin 鍐?DE 鍏ㄥ眬鎼滅储
  - 绋€鐤忓弻绐?least-squares 绮句慨
  - 鍏ㄥ垎杈ㄧ巼鍥炴姇涓庢墦鍒?

杩欎簺鍋囪鏄悊瑙ｇ粨鏋滀笌鍚庣画鎵╁睍鐨勫叧閿敋鐐癸紱鑻ュ悗缁湁鏀瑰姩锛屽繀椤诲悓姝ユ洿鏂版湰鏂囦欢銆?

## 7. Bug Ledger

褰撳墠灏氭湭纭瀹屽叏鍏抽棴鐨勯棶棰樺涓嬨€?

### 7.1 鐩綍缁撴瀯灏氭湭鏀舵暃鍒拌鑼冩€?

- 琛ㄧ幇锛?
  - 鍘熷鏁版嵁浠嶅湪 `test_data/`
  - 鏂囩尞涓庢媶瑙ｆ潗鏂欎粛鍦?`reference/`
- 褰卞搷锛?
  - 鏂?Agent 瀹规槗鍦ㄦ棫鐩綍鍜屾柊瑙勮寖涔嬮棿娣锋穯
  - 涓嶅埄浜庡悗缁嚜鍔ㄥ寲鑴氭湰绋冲畾绾﹀畾璺緞
- 褰撳墠鐘舵€侊細
  - 宸查€氳繃 `AGENTS.md` 鏄庣‘鏂拌鑼?
  - 浠撳簱瀹炰綋缁撴瀯灏氭湭杩佺Щ

### 7.2 `step02` 灏氭湭杈撳嚭缁撴瀯鍖栧弽婕旂粨鏋滄枃浠?

- 琛ㄧ幇锛?
  - 鐩墠鍙緭鍑哄浘鍍忓拰缁堢鎵撳嵃
  - 灏氭湭杈撳嚭鏍囧噯 CSV/JSON 璁板綍鏈€浣冲弬鏁板拰鎷熷悎璐ㄩ噺
- 褰卞搷锛?
  - 鍚庣画鎵归噺姣旇緝銆佸洖褰掓祴璇曞拰缁撴灉杩借釜涓嶆柟渚?
- 褰撳墠鐘舵€侊細
  - 鍔熻兘鍙敤锛屼絾缁撴灉鐣欑棔涓嶅瀹屾暣

### 7.3 褰撳墠鍙嶆紨妯″瀷铏藉凡鎵╁睍锛屼絾缁撴瀯瑙ｉ噴浠嶉潪鍞竴

- 琛ㄧ幇锛?
  - 褰撳墠宸插弽婕?`d_bulk`銆乣d_rough`銆乣ito_alpha`銆乣sigma_thickness`銆乣pvk_b_scale` 涓?`niox_k`
  - ITO/NiOx/SAM 鍘氬害涓庡鏁版潗鏂欏弬鏁颁粛鍥哄畾
- 褰卞搷锛?
  - 鍏弬鏁版敹鏁涗粛涓嶇瓑浜庣粨鏋勮В閲婂敮涓€
  - 瀵规ā鍨嬭宸笌鍙傛暟鑰﹀悎鐨勫惛鏀惰兘鍔涙湁闄?
- 褰撳墠鐘舵€侊細
  - 宸叉瘮鏃╂湡妯″瀷鏇磋兘鍚告敹琛ㄩ潰绮楃硻搴︺€佸簳灞傚惛鏀躲€佸嘲璋峰睍瀹藉拰鐭尝鏂滅巼鍋忓樊
  - 涓嶉€傚悎浣滀负鏈€缁堢墿鐞嗚В璇戠粨璁?

### 7.4 鍥惧儚鏁板瓧鍖栫粨鏋滀笉鏄師濮嬪疄楠岃〃

- 琛ㄧ幇锛?
  - `phase02_fig2_fapi_optical_constants_digitized.csv` 涓?`phase02_fig3_csfapi_optical_constants_digitized.csv` 鏉ヨ嚜璁烘枃鍥惧儚鏁板瓧鍖?
  - 涓嶆槸浣滆€呭叕寮€琛ュ厖鏉愭枡涓殑鍘熷鏁板€艰〃
- 褰卞搷锛?
  - 鍙敤浜庡鏍歌秼鍔裤€佸缓绔嬪厛楠屾垨鍋氳繎浼煎鐓?
  - 涓嶅簲琛ㄨ堪涓衡€滅粷瀵规棤璇樊鐨勫師濮嬫祴閲忔暟鎹€?
- 褰撳墠鐘舵€侊細
  - 宸蹭紭鍏堜娇鐢ㄨ鏂囧師鍥捐€岄潪鎴浘
  - 宸茶緭鍑洪噸缁樺浘涓庡彔鍔犲浘浣滀负 QA 鐣欑棔

### 7.5 PVK 甯告暟鎶樺皠鐜囦复鏃跺垎鏀凡鍏抽棴

- 琛ㄧ幇锛?
  - 鍏堝墠鐢ㄤ簬 smoke test 鐨?`n=2.45, k=0` 甯告暟閿氬畾鍒嗘敮宸蹭粠 `step02` 鍒犻櫎
- 褰卞搷锛?
  - 褰撳墠涓绘祦绋嬪凡鏀逛负娑堣垂鍩轰簬鐪熷疄 CsFAPI 鏁板瓧鍖栨暟鎹鎺ㄥ緱鍒扮殑鏍囧噯 `n-k` 涓棿浠?
  - 鈥滀复鏃跺父鏁版姌灏勭巼鈥濅笉鍐嶆槸涓绘祦绋嬮殣鍚亣璁?
- 褰撳墠鐘舵€侊細
  - 宸茶В鍐?

### 7.6 BEMA 绮楃硻灞傚崌绾х洿鎺ョ敤浜庡帇浣庣悊璁烘尟骞?

- 琛ㄧ幇锛?
  - 鍦ㄧ浉浣嶅凡缁忓熀鏈榻愮殑鍓嶆彁涓嬶紝骞虫粦鐣岄潰妯″瀷鐨勭悊璁烘尟骞呴珮浜庡疄娴嬫尟骞?
- 褰卞搷锛?
  - 寮曞叆 `PVK_Roughness` 鏈夋晥浠嬭川灞傚悗锛屾ā鍨嬪彲閫氳繃椤堕儴鍑忓弽鏁堝簲鍘嬩綆鐞嗚宄板€硷紝鏇存帴杩戝疄娴嬬害 `30%` 鐨勬尟骞呮按骞?
- 褰撳墠鐘舵€侊細
  - 宸茬撼鍏?`step02_tmm_inversion.py` 涓绘祦绋?
  - 鍚庣画浠嶉渶缁撳悎鎷熷悎缁撴灉鎸佺画楠岃瘉鎸箙鏀硅繘鏄惁绋冲畾

### 7.7 鏉＄汗褰㈢姸鐣稿彉鐨勪富瀵兼牴鍥犲凡琚畾浣嶏紝浣嗗皻鏈慨鍏ヤ富娴佺▼

- 琛ㄧ幇锛?
  - 鍦?BEMA 绮楃硻灞傚凡淇鎸箙鍚庯紝涓绘祦绋嬩粛瀛樺湪闀挎尝绔墭骞冲拰鏉＄汗璺ㄥ害澶遍厤
- 褰卞搷锛?
  - `diagnostics_shape_mismatch.py` 鐨?Probe A 鏄剧ず锛孖TO 杩戠孩澶栧惛鏀跺寮哄彲灏嗗舰鐘惰宸樉钁楀帇浣?
  - 杩欒鏄庡綋鍓嶄富娴佺▼鐨?ITO 鍚告敹寤烘ā浠嶄笉瓒筹紝鏄笅涓€杞富娴佺▼鍗囩骇鐨勪紭鍏堟柟鍚?
- 褰撳墠鐘舵€侊細
  - 宸查€氳繃 ITO 鑹叉暎鍚告敹琛ュ伩骞跺叆 `step02_tmm_inversion.py`
  - 褰撳墠涓绘祦绋嬪凡鑳芥妸闀挎尝绔墭骞虫槑鏄炬媺鍥炲疄娴嬫洸绾块檮杩?
  - 鏈疆缁х画鍔犲叆 `sigma_thickness`锛岀敤浜庡惛鏀跺厜鏂戝昂搴﹀唴鐨勫嘲璋烽挐鍖栦笌鏉＄汗灞曞

### 7.8 閾堕暅鐭洕鍏夊綊涓€鍖栦笌闀挎洕鍏変弗閲嶄笉涓€鑷?

- 琛ㄧ幇锛?
  - 瀵?`Ag_mirro-500us-1` 涓?`Ag_mirro-10ms-1` 鎸?`.spe` 鍏冩暟鎹腑鐨勭湡瀹炴洕鍏夋椂闂村仛 `Counts/ms` 褰掍竴鍖栧悗锛宍N_short / N_long` 鍏ㄦ尝娈典腑浣嶆暟绾︿负 `12.28`
  - 璇ュけ閰嶅湪 `500-600 nm`銆乣650-710 nm` 涓?`850-1055 nm` 閮芥寔缁瓨鍦紝鑰屼笉鏄彧鍙戠敓鍦ㄥ眬閮ㄩケ鍜屽嘲闄勮繎
- 褰卞搷锛?
  - 閾堕暅 HDR 鐨勭煭鏇濆厜閮ㄥ垎涓嶈兘琚涓轰笌闀挎洕鍏夊悓涓€绾挎€у搷搴旈摼璺?
  - `500-710 nm` 娉㈡鐨勭粷瀵瑰弽灏勭巼瑙ｉ噴闇€瑕佹妸璇ュけ閰嶅綋浣滈瑕?QA 椋庨櫓
- 褰撳墠鐘舵€侊細
  - 宸插湪 Phase 06 Dry Run 涓樉寮忔毚闇诧紝涓嶅仛缁忛獙缂╂斁鎴栭潪鐗╃悊淇ˉ
  - 鍚庣画闇€鍥炴煡浠櫒闂ㄦ帶銆佸鍑烘祦绋嬫垨瀹為檯鏇濆厜鏍囩

## 8. Architecture Risks

### 8.1 澶嶇敤閫昏緫妯″潡鍖栧垰鍚姩锛屼絾灏氭湭瑕嗙洊鏃ф祦绋?

- 宸叉柊澧?`src/core/hdr_absolute_calibration.py`锛岀敤浜庢敹鏁?Phase 06 鐨勬枃浠舵壂鎻忋€佹洕鍏夎В鏋愬拰 HDR 鎷兼帴閫昏緫
- 浣?`step01` 鑷?`step05` 鐨勫鐢ㄩ€昏緫浠嶅ぇ閲忔粸鐣欏湪 `src/scripts/`
- 鍚庣画鑻ョ户缁墿灞曟壒閲?HDR銆佹壒閲忓弽婕旀垨鏇村浠櫒杈撳叆鏍煎紡锛屼粛闇€缁х画鎶婃棫娴佺▼涓嬫矇鍒?`src/core/`

### 8.2 璧勬簮鏂囦欢鏍煎紡瀛樺湪闅愬紡鑴嗗急鎬?

- `ITO_20 Ohm_105 nm_e1e2.mat` 鐨勬墿灞曞悕涓庡疄闄呭彲瑙ｆ瀽鍐呭涓嶅畬鍏ㄤ竴鑷?
- 褰撳墠浠ｇ爜宸插仛 MAT/鏂囨湰鍙屽垎鏀吋瀹?
- 浣嗛暱鏈熺湅搴旇ˉ璧勬簮绱㈠紩鏂囨。锛屾槑纭瘡涓祫婧愭枃浠剁殑鐪熷疄鏍煎紡涓庢潵婧?

### 8.3 缂哄皯鍥炲綊楠岃瘉涓庢暟鍊煎熀鍑?

- 褰撳墠宸叉湁鍥惧儚缁撴灉锛屼絾缂哄皯锛?
  - 鍩哄噯鍘氬害鐨勯鏈熷尯闂?
  - 鏍囧噯杈撳叆涓嬬殑棰勬湡 `chi-square`
  - 鑷姩鍖栧洖褰掓祴璇?
- 杩欎細瀵艰嚧鍚庣画閲嶆瀯鏃惰緝闅惧垽鏂€滄ā鍨嬬湡鐨勬病鍙樷€?

### 8.4 鍥惧儚鏁板瓧鍖栭摼璺粛甯︽湁鎵嬪伐鏍囧畾鍋囪

- 褰撳墠 Fig. 2 / Fig. 3 鏁板瓧鍖栬剼鏈緷璧栧浐瀹氬浘妗嗗潗鏍囧拰鍧愭爣杞磋寖鍥?
- 鑻ュ悗缁崲鎴愭柊鐗?MinerU 鍥俱€佸師 PDF 瑁佸浘鎴栧叾浠栬鏂囧浘鐗囷紝涓嶈兘鐩存帴鍋囧畾杩欏鏍囧畾浠嶆垚绔?
- 寤鸿鍚庣画鎶婂潗鏍囨璇嗗埆鍜屽浘渚嬪墧闄よ鍒欑户缁ā鍧楀寲锛屽繀瑕佹椂鍔犲叆浜哄伐鏍℃牳姝ラ

### 8.5 PVK 鑹叉暎宸叉敼涓虹湡瀹炲厜璋卞鎺紝浣嗗鎺ㄨ竟鐣屼粛闇€瀹℃厧

- 鈥淧VK 甯告暟鎶樺皠鐜囬敋瀹氫粛灞炰复鏃堕獙璇佸亣璁锯€濊繖涓€椋庨櫓宸插叧闂?
- 褰撳墠涓绘祦绋嬪凡鍩轰簬 [LIT-0001] Fig. 3 鐨?`ITO/CsFAPI` 鏁板瓧鍖栨暟鎹紝鍦?`750-1000 nm` 閫忔槑鍖鸿繘琛?Cauchy 鎷熷悎骞跺鎺ㄥ埌 `1100 nm`
- 褰撳墠鏂板鐨勪富瑕侀闄╂槸锛?
  - `1000-1100 nm` 灞炰簬瓒呭嚭鍘熸枃娴嬮噺绐楀彛鐨勫鎺ㄥ尯
  - 褰撳墠灏?`k` 鍦ㄨ繎绾㈠鍏ㄩ儴寮哄埗涓?`0`
  - 鏁板瓧鍖栬宸細鐩存帴浼犻€掑埌 Cauchy 鍙傛暟 `A, B`
  - Phase 04 鍙堝熀浜?`1050-1100 nm` 灏炬缁х画鎶?`n` 澶栨帹鍒?`1500 nm`锛屽洜姝?`1100-1500 nm` 鐨勯娴嬬粨鏋滄洿閫傚悎鐢ㄤ綔 LOD 瓒嬪娍鍒ゆ柇锛岃€屼笉鏄洿鎺ュ綋浣滃凡楠岃瘉鏉愭枡甯告暟

### 8.6 BEMA 鍙屽弬鏁板弽婕斿瓨鍦ㄥ弬鏁扮浉鍏虫€ч闄?

- `d_bulk` 涓?`d_rough` 閮戒細褰卞搷骞叉秹鎸箙涓庣浉浣嶏紝浜岃€呭彲鑳藉瓨鍦ㄧ浉鍏虫€?
- 鍥犳鍙屽弬鏁版暟鍊兼敹鏁涗笉鑷姩绛変环浜庡敮涓€鐗╃悊瑙?
- 褰撳墠鍗囩骇鍙洿鎺ユ敼鍠勬尟骞呭尮閰嶏紝浣嗗悗缁嫢鐢ㄤ簬瀹氶噺缁撹锛屼粛闇€閫氳繃鏇村鍏堥獙鎴栨洿澶氳娴嬮噺绾︽潫鍙傛暟绌洪棿

### 8.7 ITO 鑹叉暎鍚告敹淇宸茶璇婃柇涓哄叧閿己椤?

- 鐙珛璇婃柇琛ㄦ槑锛孖TO 杩戠孩澶栧惛鏀跺寮烘瘮鍘氬害涓嶅潎鍖€鎬у拰 PVK 鑹叉暎鏂滅巼淇鏇磋兘鍚屾椂淇闀挎尝鎵樺钩涓庢暣浣撳舰鐘?
- 鏈疆涓绘祦绋嬭繘涓€姝ヨ〃鏄庯細鎶婂惛鏀舵斁澶ч檺鍒跺湪闀挎尝绔紝姣斿叏灞€鏍囬噺鍚告敹鏇寸鍚堟暟鎹?
- 鍚庣画浠嶉渶鍏虫敞 `ito_alpha` 鏄惁涓?`d_bulk` / `d_rough` 瀛樺湪鏂扮殑鍙傛暟鐩稿叧鎬?

### 8.8 瀹忚鍘氬害涓嶅潎鍖€鎬т細杩涗竴姝ユ斁澶у弬鏁扮浉鍏虫€?

- `sigma_thickness` 浼氱洿鎺ュ奖鍝嶅嘲璋峰渾娑﹀害銆佹潯绾瑰姣斿害鍜屽眬閮ㄥ舰鐘?
- 鍥犳瀹冨彲鑳戒笌 `d_rough` 鍜?`ito_alpha` 鍏卞悓鍚告敹鍚屼竴閮ㄥ垎璇樊
- 璇ユ満鍒惰兘鎻愬崌鎷熷悎鐏垫椿鎬э紝浣嗕篃浼氳繘涓€姝ュ墛寮扁€滃崟缁勫弬鏁板敮涓€瀵瑰簲鍗曚竴鐗╃悊缁撴瀯鈥濈殑鍙В閲婃€?

### 8.9 PVK 鏂滅巼鎵板姩涓?NiOx 鍚告敹浼氬紩鍏ユ柊鐨勫彲杈ㄨ瘑鎬ч闄?

- `pvk_b_scale` 浼氭敼鍙樼煭娉㈢鐩镐綅鎺ㄨ繘閫熷害涓庡嘲璋疯法搴?
- `niox_k` 浼氭敼鍙樻暣浣撳姣斿害骞朵笌 `ito_alpha` 鍏卞悓鎵挎媴瀵勭敓鍚告敹
- 鍥犳杩欎袱涓柊鑷敱搴﹁櫧鐒惰兘鏄捐憲鍘嬩綆娈嬪樊锛屼絾涔熶細杩涗竴姝ュ墛寮扁€滄嫙鍚堟渶浼樺嵆鐗╃悊鍞竴鈥濈殑鍙俊搴?

### 8.10 缁撴灉鏂囦欢鍛藉悕灏氭湭 Phase 鍖?

- 褰撳墠鍥惧儚鏂囦欢鍚嶅皻鏈樉寮忓甫涓?`phaseXX`
- 鍚庣画缁撴灉绉疮鍚庯紝鍙兘涓嶅埄浜庡杞疄楠屾瘮杈冨拰鍥炴粴瀹氫綅

### 8.11 绌烘皵闅欏亣璁惧彧瑙ｉ噴浜?bad-23 鐨勯儴鍒嗗け閰?

- `step04a_air_gap_diagnostic.py` 鍦?`bad-23` 涓婂緱鍒?`d_air 鈮?39.9 nm`锛屼笖 `chi-square` 浠?`0.03197` 闄嶅埌 `0.01619`
- 杩欒鏄?`SAM/PVK` 鐣岄潰绌烘皵闅欏苟闈炲畬鍏ㄦ棤鏁堬紝鑰屾槸鑳借В閲婁竴閮ㄥ垎璋卞舰澶遍厤
- 浣嗙敱浜?`chi-square` 浠嶉珮浜?`0.01`锛屽綋鍓嶈瘉鎹笉瓒充互鏀寔鈥滅┖姘旈殭鏄敮涓€涓诲閫€鍖栨満鍒垛€濈殑缁撹
- 鍚庣画搴斾紭鍏堟鏌ワ細
  - ITO 閫€鍖栨垨杩戠孩澶栧惛鏀舵紓绉?
  - PVK 鑹叉暎鐩稿 good 鏍峰搧鍙戠敓鏁翠綋鍋忕Щ
  - 鍏朵粬鐣岄潰鎴栧眰鍘氬弬鏁板悓鏃堕€€鍖?

### 8.12 bad-20-2 鐨勭┖闂村畾浣嶆敮鎸?L3锛屼絾鏉愭枡婕傜Щ鍚屾牱鍏抽敭

- 鍦?`bad-20-2` 涓婏紝涓夌 7 鍙傛暟绌洪棿瀹氫綅妯″瀷鐨?`chi-square` 缁撴灉鍒嗗埆绾︿负锛?
  - `L1 Glass/ITO = 0.07086`
  - `L2 ITO/NiOx = 0.06740`
  - `L3 SAM/PVK = 0.02862`
- 杩欒鏄庤嫢鍙瘮杈冪┖闂翠綅缃紝`SAM/PVK` 浠嶆槸鏈€鏈夊笇鏈涚殑绌烘皵闅欎綅缃紝涓?`d_air 鈮?40.5 nm`
- 浣?`bad-20-2` 鐨?6 鍙傛暟鍩虹嚎鏈韩绾︿负 `0.02830`锛岀暐浼樹簬閿佸畾鏉愭枡鍙傛暟鏃剁殑 `L3 7p`
- 鍙湁鍦ㄦ渶浣充綅缃笂杩涗竴姝ュ厑璁告潗鏂欏弬鏁板紱璞悗锛宍chi-square` 鎵嶉檷鍒扮害 `0.01932`
- 鍏朵腑锛?
  - `ITO Alpha` 鍙紓绉荤害 `-0.96%`
  - `PVK B-Scale` 婕傜Щ绾?`-4.26%`
  - `NiOx k` 瑙﹀強 `-15%` 涓嬭竟鐣?
- 杩欒鏄?`bad-20-2` 鐨勫紓甯镐笉鑳戒粎闈犫€滅┖姘旈殭浣嶇疆姝ｇ‘鈥濊В閲婏紝杩樹即闅忕潃鏄庢樉鐨勬潗鏂欏惛鏀?鑹叉暎婕傜Щ闇€姹?

### 8.13 Phase 06 浠嶄緷璧栦粨搴撳 OneDrive 鐩綍

- 褰撳墠 `step06_single_sample_hdr_absolute_calibration.py` 鐩存帴渚濊禆 `D:\onedrive\Data\PL\2026\0409\cor\`
- 杩欒兘婊¤冻 Dry Run锛屼絾涓嶆弧瓒抽暱鏈熷彲绉绘鎬?
- 鍚庣画搴斿敖蹇缓绔?`data/raw/phase06/` 鎴栫ǔ瀹氱殑鏁版嵁绱㈠紩鏂囨。锛岄伩鍏嶈剼鏈彧鑳藉湪褰撳墠鏈哄櫒璺緞涓婅繍琛?

### 8.14 褰撳墠瀹炴祴绐楀彛涓嶈冻浠ヨ鐩栧畬鏁?1100 nm 涓婅竟鐣?

- 鏈瀹炴祴鏁版嵁鍙鐩?`498.934-1055.460 nm`
- 鍥犳 `850-1100 nm` 鍙ｅ緞鍦ㄥ綋鍓嶆暟鎹笂鍙兘钀藉疄涓?`850-1055.460 nm`
- 鏈疆宸叉槑纭€夋嫨鈥滀笉澶栨帹琛ラ綈绐楀彛鈥濓紝浣嗗悗缁瘮杈冧笉鍚屾壒娆℃牱鍝佹椂闇€瑕佺粺涓€璇存槑杩欎竴绐楀彛鎴柇

### 8.15 Phase 06c 鐨?OneDrive 鍘熷潃瀛樻。浼氬紩鍏ュ弻浠界粨鏋滃壇鏈?

- 褰撳墠 `step06_batch_hdr_calibration.py` 鍚屾椂鍚戦」鐩洰褰曞拰 `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\` 鍐欏嚭缁撴灉
- 杩欒兘婊¤冻瀹為獙渚ф祻瑙堥渶姹傦紝浣嗕篃浼氬甫鏉モ€滃摢涓€浠芥槸鏉冨▉缁撴灉鈥濈殑缁存姢椋庨櫓
- 鍚庣画搴斿湪鏂囨。涓槑纭細椤圭洰鐩綍涓烘爣鍑嗗垎鏋愪骇鐗╋紝OneDrive 鐩綍涓哄疄楠屼晶闀滃儚瀛樻。

### 8.16 Phase 07 棣栬疆鐪熷疄鏍锋湰鍑虹幇澶氬弬鏁拌创杈?

- 褰撳墠 `DEVICE-1-withAg-P1` 涓?`DEVICE-1-withoutAg-P1` 閮藉凡瀹屾暣璺戦€?`step07_dual_window_inversion.py`
- 浣嗛杞粨鏋滄樉绀猴細
  - `ito_alpha` 涓?`pvk_b_scale` 澶氭璐磋繎涓?涓嬭竟鐣?
  - `withAg` 鏍锋湰鐨?`d_bulk` 鏇撮潬杩戜笅杈圭晫
  - `650-860 nm` 鐨?masked 娈嬪樊浠嶆槑鏄惧亸澶?
- 杩欒鏄庡綋鍓?Phase 07 宸茬粡瑙ｅ喅鈥滈摼璺兘鍚﹁窇閫氣€濈殑宸ョ▼闂锛屼絾杩樻病鏈夎В鍐斥€滅湡瀹炴牱鏈槸鍚﹀凡琚厖鍒嗙害鏉熲€濈殑鐗╃悊闂
- 鍚庣画浼樺厛妫€鏌ユ柟鍚戯細
  - `ITO / NiOx / PVK` 闀挎尝鍏堥獙鏄惁杩囩揣
  - `withAg / withoutAg` 鏄惁搴旈噰鐢ㄤ笉鍚岀殑鍙傛暟杈圭晫
  - 鏄惁闇€瑕佹妸鍚庣獥 fringe 褰㈢姸绾︽潫浠?tie-break 鎻愬崌涓烘寮忚緟鍔╂畫宸?

## 9. Recent Update Summary

- 鏇存柊鏃堕棿锛歚2026-04-13`
- 褰撳墠 Phase锛歚Phase D-1`
- 鏈鏂板/淇敼锛?
  - 鏂板 `src/scripts/stepD1_airgap_discrimination_database.py`锛屽熀浜?realistic `d_PVK + front/rear roughness` 鑳屾櫙缁熶竴鐢熸垚 `R_total` 鍒ゅ埆鏁版嵁搴?
  - 鍦?`src/core/full_stack_microcavity.py` 鏂板缁勫悎鍓嶅悜鍏ュ彛锛屽厑璁稿湪鍚屼竴 coherent stack 涓彔鍔?`front/rear BEMA background` 涓庡崟渚?`front-gap / rear-gap`
  - 鏂板 `data/processed/phaseD1/`銆乣results/figures/phaseD1/`銆乣results/logs/phaseD1/` 涓?`results/report/phaseD1_airgap_discrimination_database/`
  - 浜у嚭 case manifest銆佸叏璋卞簱銆佺獥鍙ｇ壒寰佸簱銆乺ear shift analysis銆乫amily summary 鍜?discrimination atlas
- 宸查獙璇佺粨璁猴細
  - 灞€閮?thickness nuisance 鍦?realistic background 涓婁粛涓昏琛ㄧ幇涓?rear-window fringe 鐨勯珮鍙В閲?shift
  - front / rear roughness 鏇村儚 envelope / amplitude perturbation锛岃€屼笉鏄?rigid shift
  - front-gap / rear-gap 鍙犲姞 roughness background 鍚庯紝浠嶄繚鐣欎笉鍚岀殑绐楀彛鍒嗗竷涓庨潪鍒氭€?residual 鎸囩汗
- 浠嶅緟楠岃瘉锛?
  - 杩樻病鏈夋寮忚缁冩垨姣旇緝鍒嗙被鍣紝褰撳墠鏁版嵁搴撲粛鏄畻娉曡璁鸿緭鍏ワ紝涓嶆槸鏈€缁堣瘑鍒櫒
  - composition variation 灏氭湭绾冲叆锛屽洜姝ゅ綋鍓?separability 浠呰鐩?thickness / roughness / gap 涓夌被缁撴瀯鏈哄埗
  - 浠嶆槸 specular TMM锛涙暎灏勩€乨ual-gap銆乬ap+BEMA 鑱斿悎鏈哄埗涓庡疄楠屽櫔澹版ā鍨嬪皻鏈紩鍏?

### Phase A-local Update (2026-04-13)

- Current Phase: `Phase A-local`
- Update summary:
  - 宸叉柊澧?`src/scripts/stepA_local_pvk_thickness_window.py`锛岀敤浜庡湪 `PVK surrogate v2` 涓?nominal 鍏ㄥ櫒浠剁粨鏋勪笅閲嶇粯鏇寸幇瀹炵殑灞€閮ㄥ帤搴︽寚绾瑰浘
  - 宸叉柊澧?`data/processed/phaseA_local/`銆乣results/figures/phaseA_local/`銆乣results/logs/phaseA_local/` 涓?`results/report/phaseA_local_thickness_window/`
  - 宸茬敓鎴?`phaseA_local_thickness_scan.csv`銆乣phaseA_local_thickness_feature_summary.csv`銆乣phaseA_local_deltaRtotal_heatmap.png`銆乣phaseA_local_selected_curves.png`銆乣phaseA_local_thickness_window.md` 涓?`PHASE_A_LOCAL_REPORT.md`
- Data flow:
  - `resources/aligned_full_stack_nk_pvk_v2.csv`
  - `src/core/full_stack_microcavity.py`
  - `src/scripts/stepA1_pristine_baseline.py`
  - `src/scripts/stepA_local_pvk_thickness_window.py`

### Phase D-2 Explain Update (2026-04-13)

- Current Phase: `Phase D-2`
- Update summary:
  - 宸叉柊澧?`src/scripts/stepD2b_explain_feature_pipeline.py`锛屼笓闂ㄤ负 D-2 鐨?38 涓噺鍖栫壒寰佺敓鎴愨€滃師濮嬭氨 -> 鐗瑰緛缁?-> routing鈥濊В閲婂浘
  - 宸叉柊澧?`results/report/phaseD2_quantitative_feature_dictionary/explain_feature_pipeline/`锛屽叾涓寘鍚?`feature_extraction_pipeline.png`銆乣raw_vs_feature_based_analysis.png`銆乣feature_groups_overview.png` 涓?`slide_text.md`
  - 宸叉柊澧?`results/report/phaseD2_quantitative_feature_dictionary/pptx_feature_extraction_explainer/`锛屼娇鐢?MiniMax `pptx-generator` 鐨?PptxGenJS 宸ヤ綔娴佺敓鎴?3 椤靛彲缂栬緫 `feature_extraction_explainer.pptx` 涓庨厤濂?`feature_extraction_explainer_notes.md`
  - 璇ヤ换鍔′弗鏍煎鐢?`phaseD1_rtotal_database.csv`銆乣phaseD2_quantitative_feature_database.csv`銆乣phaseD2_family_templates.csv` 涓?`PHASE_D2_REPORT.md`锛屾湭鏂板浠跨湡銆佹湭鏀圭壒寰佸畾涔夈€佹湭鍐欏叆鏂扮殑涓棿鏁版嵁搴?
- Verified conclusions:
  - 宸叉妸 D-2 鐨?38 涓壒寰佹潵婧愮ǔ瀹氭暣鐞嗕负 5 缁勶細鍒嗙獥鑳介噺銆佸悗绐楀钩绉汇€佸悗绐楅璋便€佸皬娉€佹ā鏉跨浉浼煎害
  - 宸叉槑纭缁勪細鍙ｅ緞锛歠eature extraction 鐢ㄤ簬 routing锛岃€屼笉鏄浛浠?full-spectrum fitting
  - 宸叉妸 3 寮犺В閲婂浘閲嶆帓涓?3 椤靛師鐢熷彲缂栬緫 PPT锛岃€屼笉鏄暣椤佃创鍥?
- Pending verification:
  - 褰撳墠瑙ｉ噴鍥句粛鏄眹鎶ヤ俊鎭浘锛屼笉鏄€愭楠ょ殑绠楁硶涓棿鎬佸彲瑙嗗寲锛涘鍚庣画闇€瑕佹洿缁嗙矑搴︾殑涓棿鎬佹埅鍥撅紝搴斿崟鐙墿灞曟柊鐨?report 浠诲姟
  - `data/processed/phaseA_local/phaseA_local_thickness_scan.csv`
  - `data/processed/phaseA_local/phaseA_local_thickness_feature_summary.csv`
  - `results/figures/phaseA_local/phaseA_local_deltaRtotal_heatmap.png`
  - `results/figures/phaseA_local/phaseA_local_selected_curves.png`
  - `results/logs/phaseA_local/phaseA_local_thickness_window.md`
  - `results/report/phaseA_local_thickness_window/*`
- Verified results:
  - 鎵弿鑼冨洿鍥哄畾涓?`d_PVK = 675-725 nm`锛屾闀?`1 nm`锛屽叡 `51` 涓?thickness cases
  - `R_total` 鐨勫眬閮ㄥ帤搴﹀搷搴斿湪鍓嶇獥鏈€寮憋紝鍦?`650-810 nm` 涓?`810-1055 nm` 鏄庢樉澧炲己锛屽叾涓?rear-window 鏈€澶?RMS `螖R_total` 绾︿负 `7.52%`
  - `rear_peak_nm` 鐢?`922 nm` 骞崇Щ鍒?`972 nm`锛宍rear_valley_nm` 鐢?`820 nm` 骞崇Щ鍒?`871 nm`锛岃鏄庡眬閮?thickness 鎸囩汗涓昏琛ㄧ幇涓?rear-window fringe 鐨勭郴缁熸紓绉?
- Risks / pending checks:
  - 鏈疆浠呬綔涓哄眬閮ㄥ帤搴﹁捣浼忓瓧鍏革紝涓嶅惈 roughness銆乤ir-gap銆乧omposition variation 涓?feature engineering
  - `500-900 nm` 鐨勫鑼冨洿鍘氬害鍥句粛淇濈暀涓哄叏灞€瓒嬪娍鍙傝€冿紝浣嗕笉搴旀浛浠ｆ湰杞眬閮ㄥ帤搴﹀垽鍒浘

## 10. Recommended Next Actions

寤鸿鍚庣画浼樺厛澶勭悊浠ヤ笅浜嬮」锛?

1. 浼樺厛杩涘叆 `Phase C-2 gap vs BEMA coupled comparison`锛屽湪 separation vs intermixing 涓ょ被缂洪櫡涔嬮棿寤虹珛绯荤粺娣锋穯杈圭晫
2. 骞惰璇勪及鏄惁闇€瑕佹柊澧?`Phase C-3 front-gap vs rear-gap symmetry comparison`锛屽鍓嶅悗鐣岄潰鍒嗙鏈哄埗鍋氱粺涓€褰掍竴鍖栨瘮杈?
3. 鍥炴煡 `Ag_mirro-500us` 涓?`Ag_mirro-10ms` 鐨勫綊涓€鍖栧け閰嶆潵婧愶紝浼樺厛妫€鏌ヤ华鍣ㄩ棬鎺с€佸鍑烘祦绋嬩笌瀹為檯鏇濆厜鏍囩
4. 鍩轰簬 `phase07_fit_summary.csv` 鐨勮创杈圭粨鏋滐紝閲嶆柊璇勪及 `ito_alpha`銆乣pvk_b_scale` 涓?`niox_k` 鐨勮竟鐣屽拰鍏堥獙
5. 寤虹珛 `data/raw/phase06/` 鎴栫ǔ瀹氭暟鎹储寮曪紝鎶?OneDrive 澶栭儴璺緞绾冲叆瑙勮寖鍖栧叆鍙?

## 11. Update Rule

鍚庣画鍑虹幇浠ヤ笅鎯呭喌鏃讹紝蹇呴』鏇存柊鏈枃浠讹細

- 鏂板鎴栧畬鎴愪竴涓?Phase
- 璋冩暣鐩綍缁撴瀯
- 鏂板/鍒犻櫎鍏抽敭鑴氭湰
- 鏀瑰彉涓棿鏂囦欢鏍煎紡
- 淇敼鏍稿績鐗╃悊鍋囪
- 鏂板閲嶈鏈В鍐抽棶棰樻垨鍏抽棴鏃㈡湁闂

鏇存柊鏃朵紭鍏堜繚璇侊細
- 鐩綍鏍戝噯纭?
- 鏁版嵁娴佸噯纭?
- 椋庨櫓鍜岄棶棰樺垪琛ㄥ噯纭?
- 涓嶅爢鐮屾棤鍏冲巻鍙插璇濆唴瀹?

## Phase 04c Update (2026-04-07)

- Current Phase: `Phase 04c`
- Core strategy shift: stop pursuing high-dimensional inverse fitting on `bad-20-2` absolute reflectance; use forward differential fingerprint mapping with zero-preserving normalization for morphology-only phase alignment.
- Inputs: `test_data/good-21.csv`, `test_data/bad-20-2.csv`, calibrated by step01-compatible chain.
- Baseline extraction: run 6-parameter fit on `good-21` as intact-device physical baseline (`chi-square = 0.002564`).
- Forward dictionary: lock all six baseline parameters, inject fixed `d_air = 40.0 nm` at three interfaces:
  - `L1 Glass/ITO`
  - `L2 ITO/NiOx`
  - `L3 SAM/PVK`
- Differential definitions:
  - `Delta_R_exp = bad_20_2_smooth - good_21_smooth`
  - `Delta_R_theory_L = R_theory_L - R_theory_good_6p`
- Normalization: zero-preserving normalization by `max_abs` within 850-1100 nm for both experimental and theoretical delta curves.
- Key alignment result (normalized morphology RMSE, lower is better):
  - `L1 Glass/ITO`: `1.156029`
  - `L2 ITO/NiOx`: `0.611901`
  - `L3 SAM/PVK`: `0.254985` (best)
- Phase alignment conclusion: experimental normalized differential fingerprint is best aligned with `L3 (SAM/PVK)`.

### Phase 04c Artifacts

- Script: `src/scripts/step04c_fingerprint_mapping.py`
- Figure: `results/figures/phase04c_fingerprint_mapping.png`
- Log: `results/logs/phase04c_fingerprint_mapping.md`
- Processed calibration outputs:
  - `data/processed/phase04c/good-21_calibrated.csv`
  - `data/processed/phase04c/bad-20-2_calibrated.csv`

## Phase 05 Update (2026-04-08)

- Current Phase: `Phase 05`
- Update summary:
  - 宸查€氳繃缁撴瀯鍖?Markdown 瀹屾垚鐗╃悊鍙傛暟鏁版嵁搴撹В鏋愩€?
  - 鏂板鑴氭湰 `src/scripts/step05_parse_ellipsometry_markdown.py`锛屾壂鎻?`resources/n-kdata/*/full.md`锛屼娇鐢?`BeautifulSoup` 瑙ｆ瀽 HTML 琛ㄦ牸锛屽苟杈呬互姝ｅ垯鎻愬彇姒傝鍘氬害銆?
  - 鏂板鏉愭枡鏁版嵁搴?`resources/materials_master_db.json`锛屽綋鍓嶈鐩?`C60`銆乣ITO`銆乣NIOX`銆乣sno` 鍥涚鏉愭枡銆?
  - 褰撳墠杈撳嚭瀛楁鍖呮嫭锛歚thickness_nm`銆乣rmse`銆乣wavelength_range_nm`銆乣requires_extrapolation`銆乣dispersion_models`銆乣fit_parameters`銆乣derived_parameters`銆乣parse_warnings`銆?
- Data flow:
  - `resources/n-kdata/<material>/full.md`
  - `src/scripts/step05_parse_ellipsometry_markdown.py`
  - `resources/materials_master_db.json`
- Verified results:
  - `ITO`: `Thickness = 19.595 nm`, `RMSE = 0.05936`, models = `Cauchy + Lorentz`
  - `C60`: `Thickness = 18.494 nm`, `Eg = 2.22511 eV`, models = `Tauc-Lorentz + Lorentz + Lorentz`
  - `NIOX`: `Thickness = 22.443 nm`, models = `Tauc-Lorentz + Gauss + Lorentz`
  - `sno`: `Thickness = 20.156 nm`, models = `Lorentz + Tauc-Lorentz`
  - 鍥涚鏉愭枡鐨勬姤鍛婃渶楂樻尝闀垮潎浣庝簬 `1100 nm`锛屽洜姝ゅ叏閮ㄦ爣璁?`requires_extrapolation = true`
- Dependency note:
  - Phase 05 瑙ｆ瀽閾炬柊澧炶繍琛屼緷璧?`beautifulsoup4`
- Risks / pending checks:
  - 褰撳墠 `full.md` 鏍锋湰閮借兘浠庢枃鏈拰琛ㄦ牸涓洿鎺ユ彁鍙栧叧閿弬鏁帮紝灏氭湭瑙﹀彂 `IMAGE_ONLY_ERROR`
  - 鑻ュ悗缁姤鍛婃妸鍘氬害銆佹尟瀛愬弬鏁版垨鎷熷悎璐ㄩ噺鍙繚鐣欎负 `![](images/...)` 鍥惧儚鍗犱綅锛岀幇鏈夎剼鏈細杈撳嚭 `WARNING` 骞舵妸瀵瑰簲 JSON 瀛楁鍐欎负 `null`
  - `sample_id` 浠嶄繚鐣欏師濮?Markdown 鏂囨湰锛岄儴鍒嗘姤鍛婂瓨鍦ㄦ簮鏂囦欢瀛楃缂栫爜鍣０锛屽悗缁闇€瀵规牱鍝佸悕鍋氭绱紝寤鸿澧炲姞鍗曠嫭娓呮礂瑙勫垯

## Phase 05b Update (2026-04-08)

- Current Phase: `Phase 05b`
- Update summary:
  - 宸插畬鎴?PDF 涓?JSON 鐨勪氦鍙夐獙璇侊紝鏁版嵁搴撳弻閲嶆牎楠岄€氳繃銆?
  - 鏂板鑴氭湰 `src/scripts/step05b_verify_against_pdf.py`锛岀洿鎺ヨ鍙?`resources/n-kdata/*.pdf`锛岀敤 `PyMuPDF` 鎻愬彇鏂囨湰骞朵笌 `materials_master_db.json` 鍋氬畯瑙傞敋鐐逛笌妯″瀷瀹屾暣鎬ф瘮瀵广€?
  - 鍦ㄦ暟鎹簱涓柊澧?`pdf_validation` 瀛楁锛岃褰曟瘡涓潗鏂欏搴旂殑 PDF 鏉ユ簮銆侀€氳繃鐨勬牎楠岄」銆佽嚜鍔ㄤ慨澶嶅瓧娈靛拰浜哄伐浠嬪叆瀛楁銆?
- Data flow:
  - `resources/n-kdata/*.pdf`
  - `src/scripts/step05b_verify_against_pdf.py`
  - `resources/materials_master_db.json`
- Verified results:
  - `C60`銆乣ITO`銆乣NIOX`銆乣sno` 鍧囨垚鍔熸槧灏勫埌鍞竴 PDF 婧愭枃浠躲€?
  - 鍥涚鏉愭枡鍧囬€氳繃 `thickness_nm`銆乣rmse`銆乣wavelength_range_nm` 涓?`dispersion_models` 鏍￠獙銆?
  - 褰撳墠姝ｅ紡鏁版嵁搴撴棤瀹忚閿氱偣鍐茬獊锛屾棤闇€鑷姩瑕嗗啓淇銆?
  - `requires_extrapolation` 澶嶆牳鍚庝粛鍏ㄩ儴涓?`true`锛屼笌 PDF 娉㈤暱涓婇檺 `< 1100 nm` 涓€鑷淬€?
- Dry-run repair validation:
  - 瀵逛复鏃舵祴璇?JSON 浜轰负缃┖ `ITO.thickness_nm` 鍚庯紝鑴氭湰鍙粠 `ITO.pdf` 鑷姩琛ュ洖鍘氬害銆?
  - 瀵逛复鏃舵祴璇?JSON 浜轰负娓呯┖ `NIOX` 鐨?`Gauss` 鍙傛暟鍚庯紝鑴氭湰鍙寜妯″瀷椤哄簭浠?PDF 缁撴灉鍧楄ˉ鍥?`Amp/E0/Br`銆?
- Dependency note:
  - Phase 05b 浣跨敤鐜版湁鐜涓殑 `PyMuPDF (fitz)`锛屾湭鏂板鏂扮殑 PDF 渚濊禆銆?
- Risks / pending checks:
  - PDF 琛ㄦ牸鏂囨湰鎶藉彇鍙ǔ瀹氭敮鎸佸畯瑙傞敋鐐逛笌绌哄瓧娈佃ˉ婕忥紝浣嗗宸插瓨鍦ㄧ殑澶氭尟瀛愯缁嗗弬鏁颁粛缁存寔 鈥淛SON 浼樺厛锛孭DF 浠呰ˉ婕忊€?鍘熷垯锛岄伩鍏嶈〃鏍奸敊浣嶅紩鍏ュ亣淇銆?
  - `sample_id` 鐨勫瓧绗︾紪鐮佸櫔澹颁粛鏉ヨ嚜婧愭姤鍛婃枃鏈紝鏈疆鏈仛棰濆娓呮礂銆?

## Phase 05c Update (2026-04-08)

- Current Phase: `Phase 05c`
- Update summary:
  - 宸叉柊澧?`src/scripts/step05c_build_aligned_nk_stack.py`锛屾瀯寤?`400-1100 nm`銆乣1 nm` 姝ラ暱鐨勭粺涓€娉㈤暱缃戞牸锛屽苟杈撳嚭鍙洿鎺ヤ緵 TMM 璇诲彇鐨勫叏鏍?`n-k` 琛ㄣ€?
  - 宸茬敓鎴?`resources/aligned_full_stack_nk.csv`锛岀粺涓€鍖呭惈 `Glass / ITO / NiOx / PVK / C60 / SnOx / Ag` 涓冪鏉愭枡鐨勫榻愬厜瀛﹀父鏁般€?
  - 宸茬敓鎴?`docs/images/nk_extrapolation_check.png`锛岀敤浜庝汉宸ユ牳鏌?`ITO k` 涓?`C60 n` 鍦?`900 nm` 鎷兼帴鐐归檮杩戠殑杩炵画鎬с€?
- Data flow:
  - `resources/materials_master_db.json`
  - `resources/ITO-NK鍊?csv`, `resources/NIOX-NK鍊?csv`, `resources/C60nk鍊?csv`, `resources/SNO-NK鍊?csv`
  - `data/processed/CsFAPI_nk_extended.csv`
  - `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
  - `resources/Ag.csv`
  - `src/scripts/step05c_build_aligned_nk_stack.py`
  - `resources/aligned_full_stack_nk.csv`
- Extrapolation / stitching policy:
  - `ITO / NiOx / C60 / SnOx` 鍏堝瀹炴祴鍖哄仛 cubic interpolation锛屽啀鍦ㄧ湡瀹炴祴閲忎笂鐣岀害 `900 nm` 澶勬墽琛岄暱娉㈠鎺ㄣ€?
  - `n` 灏鹃儴閲囩敤绠€鍖?Cauchy 鍏紡 `n(lambda) = A + B / lambda^2` 鎷熷悎鏈€鍚?`200 nm` 瀹炴祴鍖哄悗澶栨帹銆?
  - `k` 灏鹃儴鎸夊惎鍙戝紡鍒嗘敮澶勭悊锛?
    - `C60 / SnOx` 鍒ゅ畾涓洪€忔槑灏撅紝`900-1100 nm` 骞虫粦鏀舵暃鍒?`0`
    - `ITO` 鍒ゅ畾涓?Drude-like 涓婂崌灏撅紝淇濇寔鍗曡皟涓嶅噺
    - `NiOx` 灏鹃儴涓嶆弧瓒抽€忔槑鏉′欢锛屾寜淇濆畧涓婂崌灏剧瓥鐣ュ欢浼革紝閬垮厤闀挎尝闇囪崱
  - `PVK` 閲囩敤鍙屾簮鎷兼帴锛?
    - `750-1100 nm` 浣跨敤 `data/processed/CsFAPI_nk_extended.csv`
    - `450-749 nm` 浣跨敤 [LIT-0001] Fig. 3 鏁板瓧鍖?`ITO/CsFAPI`
    - `400-449 nm` 閫氳繃灞€閮ㄨ竟鐣屽鎺ㄨˉ榻?
  - 鎷兼帴鐐逛袱渚т娇鐢?`5 nm` 灏忕獥鍙ｅ眬閮ㄥ钩婊戯紝淇濊瘉宸ョ▼鏁版嵁琛ㄨ繛缁彲璇汇€?
- Verified results:
  - `resources/aligned_full_stack_nk.csv` 鍏?`701` 琛岋紝鍏ㄩ儴杈撳嚭鍒楁棤 `NaN/Inf`銆?
  - 杈撳嚭鍒楅『搴忓凡鍥哄畾涓猴細
    - `Wavelength_nm`
    - `n_Glass`, `k_Glass`
    - `n_ITO`, `k_ITO`
    - `n_NiOx`, `k_NiOx`
    - `n_PVK`, `k_PVK`
    - `n_C60`, `k_C60`
    - `n_SnOx`, `k_SnOx`
    - `n_Ag`, `k_Ag`
  - `Glass` 甯告暟鍒楀凡鍥哄畾涓?`n = 1.515`, `k = 0`銆?
  - `ITO` 闀挎尝 `k` 鍦?`900-1100 nm` 鍖洪棿淇濇寔鍗曡皟涓嶅噺銆?
  - `PVK` 鍦?`449/450 nm` 涓?`749/750 nm` 鎷兼帴澶勬湭鍑虹幇鏄庢樉璺冲彉銆?
- Engineering scope note:
  - 鏈疆 `Phase 05c` 鐨勯暱娉㈠鎺ㄥ睘浜庝笅娓?TMM 璇昏〃鎵€闇€鐨勫伐绋嬫暣鐞嗗眰锛屼笉绛夊悓浜庡凡缁忓畬鎴愭枃鐚害鏉熸垨瀹為獙澶嶆祴楠岃瘉鐨勬渶缁堟潗鏂欑湡鍊兼暟鎹簱銆?
- Risks / pending checks:
  - `NiOx` 闀挎尝 `k` 灏鹃儴褰撳墠鎸夊惎鍙戝紡淇濆畧寤朵几锛屽皻鏈粨鍚堥澶栨枃鐚垨鐙珛绾㈠娴嬮噺鍋氱墿鐞嗗畾鏍囥€?
  - `PVK 400-449 nm` 鏉ユ簮浜庣煭绋嬭竟鐣屽鎺紝浠呯敤浜庤ˉ榻愮粺涓€缃戞牸锛屼笉搴旂洿鎺ヤ綔涓洪珮缃俊鏉愭枡甯告暟缁撹寮曠敤銆?
  - 楠岃瘉鍥惧綋鍓嶆斁缃湪 `docs/images/` 浠ユ湇鍔＄姸鎬佹枃妗ｆ牳鏌ワ紱鑻ュ悗缁舰鎴愭壒閲忓浘琛ㄦ祦绋嬶紝寤鸿鍚屾绾冲叆 `results/figures/` 浣撶郴绠＄悊銆?

## Phase 06 Update (2026-04-08)

- Current Phase: `Phase 06`
- Update summary:
  - 宸叉柊澧?`src/core/full_stack_microcavity.py`锛屾妸 `aligned_full_stack_nk.csv` 灏佽涓哄彲鐩存帴姹傝В鐨勫叏鍣ㄤ欢寰厰鍫嗘爤妯″潡銆?
  - 宸叉柊澧?`src/scripts/step06_dual_mode_microcavity_sandbox.py`锛屾瀯寤?`Baseline / Case A / Case B` 涓夌灞傚簭锛屽苟鍦?`d_air = 0-50 nm` 涓婅緭鍑哄弻妯″紡宸垎鎸囩汗瀛楀吀銆?
  - 宸茬敓鎴?`data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv`銆乣results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png`銆乣results/figures/phase06_dual_mode_radar_map.png` 涓?`results/logs/phase06_dual_mode_microcavity_sandbox.md`銆?
- Data flow:
  - `resources/materials_master_db.json`
  - `resources/aligned_full_stack_nk.csv`
  - `src/core/full_stack_microcavity.py`
  - `src/scripts/step06_dual_mode_microcavity_sandbox.py`
  - `data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv`
  - `results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png`
  - `results/figures/phase06_dual_mode_radar_map.png`
  - `results/logs/phase06_dual_mode_microcavity_sandbox.md`
- Geometry / modeling policy:
  - `Air -> Glass` 鍓嶈〃闈㈡寜闈炵浉骞插己搴︾骇鑱斿鐞嗐€?
  - 鐜荤拑鍚庝晶钖勮啘鍫嗘爤鎸夋硶鍚戝叆灏勭浉骞?TMM 澶勭悊銆?
  - `Ag` 浣滀负鍗婃棤闄愯儗鐢垫瀬銆?
  - `d_air = 0 nm` 鏃?`Case A / Case B` 閮藉繀椤婚€€鍖栦负 `Baseline`銆?
- Verified results:
  - `Case A` 涓?`Case B` 鐨勯浂绌烘皵闅欓€€鍖栨鏌ラ€氳繃銆?
  - 鎸囩汗瀛楀吀琛屾暟婊¤冻 `71502`銆?
  - 鍙?panel 闆疯揪鍥句娇鐢ㄧ浉鍚岃壊鏍囷紝婊¤冻 A/B 褰㈡€佸姣旈渶姹傘€?
- Risks / pending checks:
  - `400-650 nm` 鍦ㄦā鍨嬩腑涓嶄細琚汉涓烘竻闆讹紝鏄惁鍦ㄥ疄楠屼笂杩戜技闆跺搷搴斾粛闇€鍚庣画鏁版嵁楠岃瘉銆?
  - `NiOx` 闀挎尝 `k` 涓?`PVK 400-449 nm` 鐨勫伐绋嬭ˉ榻愰闄╀細鐩存帴浼犻€掑埌 `Phase 06` 鐨勭粷瀵瑰箙鍊煎垽鏂€?
  - 褰撳墠缁撴灉鏇撮€傚悎浣滀负缂洪櫡妯″紡鎸囩汗瀛楀吀锛岃€岄潪鐩存帴褰撲綔宸查獙璇佺殑鏉愭枡鐪熷€肩粨璁恒€?

## Phase 07 Update (2026-04-08)

- Current Phase: `Phase 07`
- Update summary:
  - 宸查噸鏋?`src/core/full_stack_microcavity.py`锛屽皢 `front/back` 鐣岄潰瀹氫箟銆佸帤搴﹁鐩栧拰浠绘剰娉㈤暱鎻掑€肩粺涓€灏佽鍒?`forward_model_for_fitting()`銆?
  - 宸叉柊澧?`src/scripts/step07_orthogonal_radar_and_baseline.py`锛岃緭鍑?pristine 涓夊垎鍖哄熀鍑嗗浘涓?`front/back` 姝ｄ氦闆疯揪鍥俱€?
  - 宸茬敓鎴?`data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv`銆乣results/figures/phase07_baseline_3zones.png`銆乣results/figures/phase07_orthogonal_radar.png` 涓?`results/logs/phase07_orthogonal_radar_diagnostic.md`銆?
- Data flow:
  - `resources/aligned_full_stack_nk.csv`
  - `resources/materials_master_db.json`
  - `src/core/full_stack_microcavity.py`
  - `src/scripts/step07_orthogonal_radar_and_baseline.py`
  - `data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv`
  - `results/figures/phase07_baseline_3zones.png`
  - `results/figures/phase07_orthogonal_radar.png`
  - `results/logs/phase07_orthogonal_radar_diagnostic.md`
- Verified results:
  - `forward_model_for_fitting()` 鐨勪竴缁存暟缁勮緭鍏ヨ緭鍑哄绾﹂獙璇侀€氳繃銆?
  - `front/back` 鍦?`d_air = 0 nm` 鏃堕兘鑳戒弗鏍奸€€鍖栦负 pristine baseline銆?
  - `Phase 07` 鎸囩汗瀛楀吀琛屾暟婊¤冻 `71502`銆?
  - `front` 鍦?`Zone 1` 鐨?`max|螖R| 鈮?28.16%`锛宍back` 浠呯害 `0.71%`锛屽畯瑙傛浜ょ壒寰佹槑纭垚绔嬨€?
- Risks / pending checks:
  - `Zone 2` 褰撳墠鍙湪鏂囨。鍜屽浘涓爣璁颁负鍚庣画闆舵潈閲嶅尯锛屽皻鏈湡姝ｈ繘鍏ヤ紭鍖栧櫒瀹炵幇銆?
  - `NiOx` 闀挎尝 `k` 涓?`PVK 400-449 nm` 鐨勫伐绋嬪鎺ㄩ闄╀粛浼氬奖鍝?`Phase 07` 鐨勭粷瀵瑰箙鍊笺€?
  - 褰撳墠缁撹閫傚悎浣滀负鍓嶅悗鐣岄潰瀹忚鍒ゅ埆涓?LM 鏋舵瀯璁捐渚濇嵁锛屽皻涓嶈兘鏇夸唬鍚庣画瀹為獙鎷熷悎楠岃瘉銆?

## Phase 07 Implementation Update (2026-04-10)

- Current Phase: `Phase 07`
- Update summary:
  - 宸叉柊澧?`src/core/phase07_dual_window.py`锛屽皢 Phase 07 鐨勫叏鏍?forward model銆佸弻绐楁畫宸€丆60 瀹堟亽銆佸悗绐?basin 鎵弿銆丏E 鍏ㄥ眬鎼滅储銆乴east-squares 绮句慨鍜屽洓绫诲浘琛ㄨ緭鍑虹粺涓€灏佽銆?
  - 宸叉柊澧?`src/scripts/step07_dual_window_inversion.py`锛屾敮鎸佲€滃師濮嬪鏇濆厜浼樺厛锛宍*_hdr_curves.csv` 鍥為€€鈥濈殑鍙屽叆鍙ｆ暟鎹绾裤€?
  - 宸插缓绔?`data/processed/phase07/fit_inputs/`銆乣data/processed/phase07/fit_results/`銆乣results/figures/phase07/` 涓?`results/logs/phase07/` 鐨勬爣鍑嗚緭鍑虹洰褰曘€?
  - 宸茬敓鎴?`phase07_source_manifest.csv`銆乣phase07_fit_summary.csv`銆佷袱渚嬫牱鏈殑閫愭尝闀挎嫙鍚堣〃銆佷紭鍖栨棩蹇楀拰 8 寮犺瘖鏂浘銆?
- Data flow:
  - `test_data/phase7_data/*_hdr_curves.csv`
  - `src/scripts/step07_dual_window_inversion.py`
  - `src/core/phase07_dual_window.py`
  - `data/processed/phase07/fit_inputs/*_fit_input.csv`
  - `data/processed/phase07/fit_results/*_fit_curve.csv`
  - `data/processed/phase07/fit_results/*_fit_summary.csv`
  - `results/figures/phase07/*`
  - `results/logs/phase07/*_optimizer_log.md`
- Verified results:
  - `C60` 瀹堟亽妫€鏌ラ€氳繃锛歚d_rough = 0/10/20/30 nm` 鏃讹紝`d_C60_bulk = 15/10/5/0 nm`銆?
  - `withAg / withoutAg` 涓ょ缁堢杈圭晫涓嬶紝鍓嶅悜妯″瀷鍧囪繑鍥炴湁闄愪笖 `0-1` 鑼冨洿鍐呯殑鍙嶅皠鐜囥€?
  - 涓や釜鐜版湁 `Phase 07` 鏍锋湰閮藉凡瀹屾暣璺戦€氭嫙鍚堜笌钀界洏娴佺▼銆?
  - 鍓嶇獥涓庡悗绐楃殑绐楀彛灏哄害鍧囨湭瑙﹀彂灏忎簬 `0.005` 鐨勬潈閲嶇垎鐐搞€?
- Risks / pending checks:
  - `DEVICE-1-withAg-P1` 涓?`DEVICE-1-withoutAg-P1` 褰撳墠閮藉嚭鐜颁笉鍚岀▼搴︾殑璐磋竟瑙ｏ紝璇存槑鐪熷疄鏍锋湰鐨勫弬鏁扮┖闂翠粛鏈鍏呭垎绾︽潫銆?
  - `650-860 nm` 鐨?masked 娈嬪樊浠嶇劧杈冨ぇ锛屽綋鍓嶅彧琚В閲婁负 PL/妯″瀷澶遍厤褰㈡€侊紝杩樻湭杩涘叆鏇村己鐨勮儗鏅缓妯°€?
  - 闇€瑕佽繘涓€姝ュ垽鏂?`withAg / withoutAg` 鏄惁蹇呴』閲囩敤涓嶅悓杈圭晫鎴栨洿寮哄厛楠屻€?

## Phase 07 Z-Score Rear-Window Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 宸插皢 `src/core/phase07_dual_window.py` 鐨勫悗绐楁畫宸粠鈥滅粷瀵瑰弽灏勭巼鍔犳潈宸€濆垏鎹负鈥淶-Score 褰㈡€佸樊鈥濓紝鍓嶇獥 `500-650 nm` 浠嶄繚鎸佺粷瀵瑰€兼畫宸€?
  - 宸叉仮澶?`ito_alpha` 鐨勯粯璁よ竟鐣屽埌 `[0.0, 5.0]`锛岄伩鍏嶅悗绐楁瀬寮变俊鍙蜂笅鐢辩粷瀵瑰己搴﹁宸妸 ITO 闀挎尝鍚告敹寮鸿鎸ゅ埌闈炵墿鐞嗗尯鍩熴€?
  - 宸叉柊澧?`src/scripts/step07_zscore_sanity_check.py`锛岀敤浜庡 `DEVICE-1-withAg-P1` 鎵ц鍚庣獥宄拌胺鐗╃悊鑷瘉銆佽緭鍑哄钩婊戝姣斿浘锛屽苟鐩存帴璺戦€?Z-Score 鐗堟湰鎷熷悎銆?
- Data flow:
  - `test_data/phase7_data/DEVICE-1-withAg-P1_hdr_curves.csv`
  - `src/scripts/step07_zscore_sanity_check.py`
  - `src/core/phase07_dual_window.py`
  - `results/figures/phase07/phase07_device_1_withag_p1_rear_sanity_check.png`
  - `results/figures/phase07/phase07_device_1_withag_p1_dual_window_zoom.png`
  - `data/processed/phase07/fit_results/phase07_device_1_withag_p1_fit_summary.csv`
- Verified results:
  - 鍚庣獥 `860-1055 nm` 缁忓己骞虫粦鍚庤瘑鍒埌涓€缁勪富鏋佸€硷細`lambda_peak = 870.774 nm`锛宍lambda_valley = 1034.331 nm`銆?
  - 鍩轰簬 `aligned_full_stack_nk.csv` 涓?`PVK` 鎶樺皠鐜囨彃鍊煎緱鍒?`n_avg = 2.4289`锛岀浉閭诲嘲璋峰叕寮忕粰鍑?`d_estimate = 566.8 nm`銆?
  - 璇ュ€肩暐浣庝簬鍘熷厛棰勬湡鐨?`600-800 nm`锛屼絾浠嶅鍦ㄥ悓涓€閲忕骇锛岃鏄庡悗绐椾粛淇濈暀鍙В閲婄殑骞叉秹褰㈡€佷俊鎭紝閫傚悎缁х画鐢ㄤ簬鐩镐綅/褰㈡€佸绾︽潫銆?
  - Z-Score 鎷熷悎鍚庯紝`DEVICE-1-withAg-P1` 鐨勬渶浣宠В钀藉湪 `d_bulk = 810.3 nm`锛屽悗绐楁畫宸垚鏈檷涓?`0.0238`锛屽彸渚у弻绐楀浘宸叉敼涓?`z_meas / z_model` 鐩存帴瀵规瘮銆?
- Risks / pending checks:
  - 褰撳墠宄拌胺鎺ㄧ畻鍘氬害 `566.8 nm` 涓?Z-Score 鎷熷悎鏈€浼?`d_bulk = 810.3 nm` 浠嶅瓨鍦ㄦ樉钁楀亸宸紝鎻愮ず鈥滃崟涓€宄拌胺鍏紡鈥濅笌鈥滃灞傚畬鏁?TMM 鐩镐綅鈥濅箣闂翠粛鏈夌郴缁熷樊銆?
  - `rear_derivative_correlation` 浠嶅亸浣庯紝璇存槑鍚庣獥铏芥湁褰㈡€佷俊鎭紝浣嗗櫔澹般€侀暱娉㈣壊鏁ｄ笌澶氬眰鑰﹀悎浠嶅湪鍓婂急鐩镐綅閿佸畾鑳藉姏銆?
  - `pvk_b_scale` 缁х画璐村湪涓嬬晫锛屽悗缁粛闇€璇勪及鏄惁搴旇繘涓€姝ユ敹绱?PVK 闀挎尝鑹叉暎鍏堥獙锛屾垨涓哄悗绐楀鍔犳洿绋冲畾鐨勫寘缁?棰戝煙绾︽潫銆?

## Phase 07 Baseline Finalization Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 宸插皢 `src/core/full_stack_microcavity.py` 鐨勯粯璁ゅ嚑浣曞彛寰勫悓姝ヤ负 `Glass / ITO(100) / NiOx(45) / SAM(5) / PVK(700) / C60(15) / Ag(100) / Air`锛岀粓姝㈡棫 `19.595/22.443/500/18.494` 榛樿鍊间笌 Phase 07 涓婚摼璺苟瀛樼殑娣蜂贡銆?
  - 宸插湪 `src/core/phase07_dual_window.py` 涓柊澧?`front_scale` 鍙傛暟锛屼粎浣滅敤浜庡墠绐?`500-650 nm` 鐨勮娴嬪眰鍙嶅皠鐜囷紝鐢ㄤ簬鍚告敹绉垎鐞?鎺㈠ご鏈畬鏁存敹闆嗛暅闈㈠弽灏勬墍瀵艰嚧鐨勫畯瑙傚嚑浣曟紡鍏夈€?
  - 宸插皢鍏ㄨ氨璇婃柇鍥剧殑 `650-860 nm` masked 鍖烘敼涓轰粎瑙嗚鐢ㄩ€旂殑骞虫粦妗ユ帴锛屼笉鍙備笌 cost 璁＄畻銆?
- Verified results:
  - 浣跨敤鐪熷疄鏍锋湰 `DEVICE-1-withAg-P1` 閲嶆柊鎷熷悎鍚庯紝鍓嶇獥 cost 浠庢棫鐗堢殑鏁伴噺绾ф樉钁楀帇浣庤嚦 `0.0122`锛屽悗绐?Z-Score cost 涓?`0.0142`锛屾€?cost 涓?`0.0264`銆?
  - 鏈€浼樺墠绐楀嚑浣曠缉鏀句负 `front_scale = 0.2172`锛屼笌鍓嶆湡鐙珛鎺㈡祴寰楀埌鐨?`~0.22` 涓€鑷达紝鏀寔鈥滃墠绔嚑浣曟敹闆嗘晥鐜囨崯澶扁€濊€岄潪鈥滄潗鏂欏惛鏀剁己澶扁€濈殑瑙ｉ噴銆?
  - 鍚庣獥鏈€浣宠В浠嶈惤鍦?`d_bulk = 815.3 nm`锛岃鏄?`front_scale` 鏈牬鍧忓悗绐楀舰鎬佸閿佺浉銆?
  - `full_stack_microcavity.py` 鍑犱綍鍚屾鍚庡凡閫氳繃鍓嶅悜鍐掔儫锛岄粯璁ゅ帤搴﹁緭鍑轰负 `100/45/5/700/15/100 nm`銆?
- Risks / pending checks:
  - `front_scale` 鏄娴嬪嚑浣曚慨姝ｏ紝涓嶆槸鏉愭枡鍙傛暟锛涘叾瀛樺湪鎰忓懗鐫€褰撳墠缁濆鍙嶅皠鐜囬摼璺粛鏈畬鍏ㄩ棴鍚堝埌鈥滄棤鍑犱綍鎹熷け鈥濈殑瀹為獙鍙ｅ緞銆?
  - `ito_alpha`銆乣niox_k`銆乣pvk_b_scale` 浠嶈创杈癸紝璇存槑鍓嶅悗绐椾箣闂翠粛鏈夌粨鏋?鑹叉暎閫€鍖栵紝闇€瑕佸湪 Phase 08 鍓嶅悜鎺激娌欑洅涓户缁媶鍒嗐€?
  - masked 鍖哄钩婊戞ˉ鎺ヤ粎鐢ㄤ簬瑙嗚杩炵画鎬э紝涓嶈兘琚В閲婁负鐪熷疄 PL 鑳屾櫙妯″瀷銆?

## Phase 07 Diagnostic Sandbox Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 宸叉柊澧?`src/scripts/step07_sandbox_probe_a.py`锛岀敤浜庡湪閿佹鍓嶅満鍑犱綍涓庨浂 Debye-Waller 鐨勬潯浠朵笅锛屽崟鐙帰娴嬪墠绐楃煭娉㈤檮鍔犲惛鏀舵槸鍚﹁兘瑙ｉ噴 `500-650 nm` 骞呭€煎け閰嶃€?
  - 宸叉柊澧?`src/scripts/step07_sandbox_probe_b_heatmap.py`锛岀敤浜庡湪閿佸畾褰撳墠 Stage 1 缁撴灉鍚庯紝瀵瑰悗绐?`d_bulk` 涓?`pvk_b_scale` 鍋氫簩缁寸綉鏍兼壂鎻忓苟杈撳嚭 Z-Score Cost 鐑姏鍥俱€?
- Verified results:
  - Probe A 鏄庣‘鍙嶉┏浜嗏€淣iOx 鐭尝缂哄惛鏀垛€濊繖涓€涓诲亣璇达細`NiOx` 棰濆鐭尝鍚告敹鐨勬渶浼樿В鍑犱箮涓?`0`锛屼笖鏃犳硶闄嶄綆鍓嶇獥 cost锛沗ITO` 棰濆鐭尝鍚告敹鑳介儴鍒嗘敼鍠勫墠绐楋紝浣嗗崟鍙傛暟鏈€浼?cost 浠嶈繙楂樹簬鐩爣绾匡紝璇存槑鍓嶇獥澶遍厤涓嶈兘琚崟涓€灞€閮ㄥ惛鏀堕」瑙ｉ噴銆?
  - Probe B 鐨勫悗绐楃儹鍔涘浘鏄剧ず锛氬叏灞€鏈€灏忓€间綅浜?`d_bulk 鈮?630 nm`銆乣pvk_b_scale = 0.5` 鐨勬壂鎻忚竟鐣岋紱璋峰簳杞ㄨ抗杩戜箮绔栫洿锛岃鏄庡綋鍓嶄富瀵奸棶棰樹笉鏄吀鍨嬪己 `n-d` 鏂滃悜绠€骞讹紝鑰屾洿鍍?`pvk_b_scale` 琚暣浣撴帹鍚戜綆杈圭晫鍚庯紝`d_bulk` 鍦ㄧ害 `630 nm` 闄勮繎褰㈡垚灞€閮ㄥ惛寮曠泦銆?
- Risks / pending checks:
  - 鍓嶇獥闂鏇村儚鈥滅己澶辩殑鍓嶇鐗╃悊鏈哄埗鈥濇垨鈥滃惛鏀朵綅缃?褰㈠紡涓嶅鈥濓紝鑰屼笉鏄畝鍗曠殑 `NiOx k` 涓嶈冻銆?
  - 鍚庣獥闂鏆傛湭鏄剧ず鍑洪鎯充腑鐨勯暱鏂滆胺锛屾彁绀哄悗缁洿搴斾紭鍏堟敹绱?`pvk_b_scale` 鍏堥獙銆佹鏌ラ暱娉㈡姌灏勭巼鍙ｅ緞锛岃€屼笉鏄洸鐩妸 `d_bulk` 涓?`pvk_b_scale` 涓€璧风户缁斁瀹姐€?

## Phase 07 Sandbox Probe D Audit Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 宸叉柊澧?`src/scripts/step07_sandbox_probe_d_audit.py`锛岀敤浜庡 `DEVICE-1-withAg-P1` 鍦?`550 nm` 澶勬墽琛屽弻璺嚎娉曞尰瀛﹀鏌ワ細涓€鏉℃瀬绠€鍓嶈〃闈㈢悊璁烘绠楋紝涓€鏉′粠 0409 鍘熷 `*-cor.csv + .spe` 閲嶅缓 HDR 骞舵墜宸ュ绠楃粷瀵瑰弽灏勭巼銆?
  - 宸茶緭鍑?`results/logs/phase07/phase07_device_1_withag_p1_sandbox_probe_d_audit.md` 涓?`results/figures/phase07/phase07_device_1_withag_p1_sandbox_probe_d_theory_audit.png`銆?
- Verified results:
  - Theory audit 瀵?`Air -> Glass(incoherent) -> ITO(100) -> NiOx(45) -> PVK(semi-infinite)` 鍦?`550 nm` 缁欏嚭 `R_total = 11.889%`锛涘叾涓崟鐙?`Air/Glass` Fresnel 鍓嶈〃闈㈢害涓?`4.193%`銆?
  - Calibration audit 浠?0409 鍘熷鏂囦欢閲嶅缓鍚庯紝鍦?`550.147 nm` 澶勫緱鍒帮細
    - 鏍峰搧鍘熷鍧囧€硷細`32617.83 counts @ 150 ms`锛宍64895.00 counts @ 2000 ms`
    - 閾堕暅鍘熷鍧囧€硷細`40565.95 counts @ 0.5 ms`锛宍64899.00 counts @ 10 ms`
    - 鍘傚閾堕暅鍙嶅皠鐜囷細`97.454%`
  - 鑻ョ洿鎺ュ拷鐣?HDR 瀵归綈锛屼粎鎸夊師濮?`Counts/Time` 鎵嬬畻锛屽垯寰楀埌锛?
    - `short-short = 0.261%`
    - `long-long = 0.487%`
  - 浣嗘寜 HDR 瀵归綈鍚庣殑瀹為檯娴佹按绾垮彛寰勬墜宸ュ绠楋細
    - `manual_hdr = 2.671%`
    - 涓庡悓鎵瑰師濮嬫枃浠堕噸寤哄嚭鐨?`2.671%` 瀹屽叏涓€鑷?
    - 涓庡鍑?`hdr_curves.csv` 涓殑 `2.710%` 浠呭樊绾?`0.039` 涓櫨鍒嗙偣
  - 杩欒鏄庡綋鍓?Phase 06/07 鏍″噯浠ｇ爜鍦?`550 nm` 澶勬槸绠楃悊鑷唇鐨勶紱涓嶅瓨鍦ㄦ妸鐞嗚 `~10%` 閿欑畻鎴?`~2.5%` 鐨勯殣钘忔洕鍏夋椂闂磋В鏋?Bug銆傜浉鍙嶏紝鑻ヤ笉鍋?HDR 鏇濆厜瀵归綈锛屽弽灏勭巼浼氭洿浣庛€?
- Risks / pending checks:
  - `11.889%` 鐨勭悊鎯虫鍙嶅皠妯″瀷涓?`2.67%` 鐨勫疄楠屾牎鍑嗗€间箣闂翠粛瀛樺湪绾?`4.45x` 鐨勫樊璺濓紱杩欐洿绗﹀悎瑙傛祴鍑犱綍 NA 鎴柇銆佹暎灏勬紡鍏夋垨闀滈潰鏀堕泦鎹熷け锛岃€屼笉鏄綋鍓嶄唬鐮佸叕寮忛敊璇€?
  - 閾堕暅鐭洕鍏変笌闀挎洕鍏変箣闂翠粛瀛樺湪鏄捐憲缁忛獙瀵归綈鍥犲瓙锛岃鏄庝华鍣ㄧ煭鏇濆厜閾捐矾涓嶈兘鐩存帴鎸?`Counts/Time` 瑙嗕负涓庨暱鏇濆厜涓ユ牸鍚屽彛寰勩€?

## Phase 09 Update (2026-05-07)

- Current Phase: `Phase 09`
- Update summary:
  - 已新增 `docs/architecture/*.md` 与 `docs/tools/*.md`，明确正式工具平台分层、core 沙箱、domain 命名、IO adapter、GUI 技术栈和输出约定。
  - 已新增 `src/common/`、`src/domain/`、`src/storage/`、`src/workflows/`、`src/visualization/`、`src/gui/common/` 最小骨架。
  - 已新增 `SpectrumData`、`QCSummary`、`ToolRunManifest`、`SpectrumReaderRegistry` 等基础对象。
  - 已明确新 GUI 默认技术路线为 `PySide6 + pyqtgraph`，但本轮未实现具体 GUI 业务。
- Verified results:
  - 最小 domain model 与 reader registry 已具备独立单元测试骨架。
  - `requirements.txt` 已补充 `PySide6`、`pyqtgraph`、`pytest`，用于未来 GUI 与测试层准备。
- Risks / pending checks:
  - 旧 `src/core` 与 `src/scripts` 仍存在逐步迁移需求。
  - `storage/readers` 与 `storage/writers` 目前只有 protocol 和 registry 骨架，尚无正式 CSV/H5/Zarr 实现。
