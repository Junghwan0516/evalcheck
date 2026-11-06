"""Presentation-only English/Korean messages. Never translate source/data values."""
from html.parser import HTMLParser
import html
import re

KO = {
'Find the line.':'원인 코드를 찾고,','Fix the split.':'데이터 분할을 바로잡으세요.',
'Find the line behind':'평가 위험을 만드는','the evaluation risk.':'원인 코드를 확인하세요.',
'Before you trust the score,':'모델 점수를 믿기 전에,','inspect the split.':'데이터 분할부터 확인하세요.',
'EVALUATION RISKS, MADE VISIBLE':'평가 위험을 근거와 함께 확인하세요',
'EVALUATION INTEGRITY':'평가 신뢰성 검사',
'Notebook → evidence → CI gate':'노트북 → 근거 확인 → CI 검사',
'LOCAL ANALYSIS · v0.5':'로컬 분석 · v0.5',
'Trace risky notebook code and overlapping data back to the exact evidence. Inspect locally, then take the same Python engine into CI.':'노트북의 위험 코드와 데이터 겹침을 원문까지 추적합니다. 기기 안에서 검사하고, 같은 Python 엔진을 CI에서도 사용하세요.',
'One engine. Two entry points.':'하나의 엔진, 두 가지 사용 방식',
'Python CLI + browser WebAssembly':'Python 명령줄 + 브라우저 WebAssembly',
'Notebook source is parsed, never executed.':'대상 노트북 코드는 분석만 하며 실행하지 않습니다.',
'No API key. No file upload to a server.':'API 키 없이 사용하며 입력 파일을 서버로 보내지 않습니다.',
'01 / Choose your evidence':'01 / 검사할 자료 선택',
'02 / Inspect the evidence':'02 / 검사 근거 확인',
'No sign-up':'가입 없이 사용',
'Notebook / Python':'노트북 / Python',
'Train / test data':'학습 / 시험 데이터',
'START WITH A REPRODUCIBLE EXAMPLE':'재현 가능한 예제로 시작하세요',
'Leaky notebook':'누출이 있는 노트북','Fixed notebook':'수정한 노트북',
'Real public data · 3,000 rows':'실제 공개 데이터 · 3,000개 행','Synthetic issues':'문제를 넣은 합성 예제',
'Drop a notebook or Python file':'노트북 또는 Python 파일을 놓으세요',
'.ipynb or .py · up to 2 MB each':'.ipynb 또는 .py · 파일당 최대 2 MB',
'Drop two files: train, then test':'학습 파일, 시험 파일 순서로 두 개를 놓으세요',
'.csv or .jsonl · training file first':'.csv 또는 .jsonl · 학습 파일을 먼저 선택',
'Choose local file':'내 파일 선택',
'Notebook preview · source order':'노트북 미리보기 · 저장된 셀 순서',
'Python editor · parsed, never executed':'Python 편집기 · 분석만 하며 실행하지 않음',
'Edit as Python':'Python으로 편집',
'Python source or notebook preview':'Python 코드 또는 노트북 미리보기',
'Load two CSV / JSONL files: training first, then test.':'CSV / JSONL 파일 두 개를 학습, 시험 순서로 불러오세요.',
'Text column':'텍스트 열','Label column':'라벨 열',
'Isolation group (optional)':'분리할 그룹 (선택)','Source identifier (optional)':'원본 식별자 (선택)',
'Jaccard threshold':'자카드 유사도 기준',
'Lexical overlap is review evidence, not proof of score inflation. Browser limit: 5,000 rows per file; 200,000 comparisons.':'어휘 겹침은 검토 근거이며 점수 과장의 증거를 뜻하지는 않습니다. 브라우저 제한: 파일당 5,000행, 유사도 비교 200,000회.',
'Scan locally →':'내 기기에서 검사 →','Cancel':'중단',
'Ready. Try the leaky notebook, then the fixed version.':'준비됐습니다. 누출 예제를 검사한 뒤 수정본과 비교해 보세요.',
'Ready. Scan this notebook, then compare the fixed version.':'준비됐습니다. 이 노트북을 검사한 뒤 수정본과 비교해 보세요.',
'Your files stay in this browser.':'입력 파일은 이 브라우저 안에서 처리됩니다.',
'First scan downloads a pinned Python WebAssembly runtime from jsDelivr. Internet access is needed for that bootstrap; file contents are not sent there. Cancel terminates the analysis worker.':'첫 검사에서는 jsDelivr에서 고정 버전 Python WebAssembly 런타임을 받으므로 인터넷이 필요합니다. 입력 파일 내용은 전송하지 않습니다. 중단하면 분석 워커를 종료합니다.',
'Local file input':'로컬 파일 입력','Inspection mode':'검사 종류',
'Inputs':'입력','Files inspected':'검사한 파일','Findings to review':'검토할 항목',
'Findings':'검사 항목','Scope notes':'분석 범위 안내','Records inspected':'검사한 행',
'Overlap rows':'겹침에 관련된 행',
'Supported static patterns and lexical matches require review. Zero findings is not a leakage-free certification.':'지원하는 코드 패턴과 어휘 겹침은 맥락 검토가 필요합니다. 발견 항목이 0개여도 모든 누출이 없다는 인증은 아닙니다.',
'Search evidence':'검사 근거 검색','Filter findings':'검사 항목 필터',
'Search rule, source, text or row…':'규칙·원본·텍스트·행 검색…','All findings':'모든 항목',
'A score deserves evidence.':'평가 점수에도 근거가 필요합니다.',
'Run an example or inspect your own files.':'예제를 실행하거나 내 파일을 검사해 보세요.',
'Findings will show the source and the observed use.':'검사 결과에 원인과 사용 지점을 함께 표시합니다.',
'Coverage and limitations':'분석 범위와 한계',
'Evidence you can reproduce':'직접 재현할 수 있는 근거',
'A fixed synthetic negative control exposed inflated evaluation scores:':'고정한 합성 잡음 실험에서 평가 점수 부풀림을 재현했습니다:',
'79.5% with leaked feature selection vs 51.6% with a training-only Pipeline':'전체 자료에서 특성을 선택하면 79.5%, 학습 자료에서만 선택한 Pipeline은 51.6%',
', averaged across ten noise datasets. This is not a real-world effect estimate.':'이며 잡음 데이터 10개의 평균입니다. 실제 서비스에서의 효과 크기를 추정한 값은 아닙니다.',
'Detection, with its limits included':'놓친 사례까지 포함한 탐지 결과',
'On 40 authored cases: 20 risks detected, 4 missed, 16 safe cases unflagged. Unsupported risks remain in overall recall. This is not independent real-world validation.':'자체 작성 40개 사례에서 위험 20개를 탐지하고 4개를 놓쳤으며, 정상 16개에는 경고가 없었습니다. 지원 범위 밖의 위험도 전체 재현율에 포함합니다. 독립적인 실사용 검증 결과는 아닙니다.',
'Move the check into your workflow':'개발 작업에도 검사를 연결하세요',
'Export HTML / JSON / SARIF. Pre-commit and a reusable GitHub Actions gate are included in the source project. Hosted GitHub integration has not yet been exercised.':'HTML / JSON / SARIF를 출력합니다. 소스에 pre-commit과 재사용 가능한 GitHub Actions 설정이 포함됩니다. 실제 GitHub 서버 연동은 아직 검증하지 않았습니다.',
'Open-source software: MIT. Public sentiment example: Kotzias (2015), UCI DOI 10.24432/C57604, CC BY 4.0. Pyodide: MPL-2.0. No analytics or application backend.':'소프트웨어: MIT. 공개 감성분석 예제: Kotzias (2015), UCI DOI 10.24432/C57604, CC BY 4.0. Pyodide: MPL-2.0. 분석용 추적 도구와 애플리케이션 백엔드를 사용하지 않습니다.',
'Run the current input to see its evidence.':'현재 입력을 검사하면 근거를 확인할 수 있습니다.',
'Real public data, example-authored seed-42 split. Loading columns…':'실제 공개 데이터에 예제용 시드 42 분할을 적용했습니다. 열을 불러오는 중…',
'Synthetic example with intentionally planted issues.':'문제를 의도적으로 넣은 합성 예제입니다.',
'None':'선택 안 함','TRAIN':'학습','TEST':'시험','train':'학습','test':'시험','development':'개발 검증',
'TRAIN {train} records · TEST {test} records. Confirm the column mapping below.':'학습 {train}행 · 시험 {test}행. 아래에서 열 설정을 확인하세요.',
'Inputs parsed locally. Confirm columns, then scan.':'기기 안에서 입력을 읽었습니다. 열 설정을 확인한 뒤 검사하세요.',
'Loading the pinned Python WebAssembly runtime. Your files stay in this worker.':'고정 버전 Python WebAssembly 런타임을 불러오는 중입니다. 입력 파일은 이 워커 안에서 처리됩니다.',
'Inspecting locally with the same Python engine as the CLI…':'CLI와 같은 Python 엔진으로 기기 안에서 검사 중…',
'Runtime bootstrap failed':'런타임을 불러오지 못했습니다',
'No findings match these filters.':'선택한 필터에 맞는 항목이 없습니다.',
'No supported finding observed. Review coverage and limitations.':'지원 범위 안에서 발견한 항목이 없습니다. 분석 범위와 한계를 확인하세요.',
'{visible} matching findings / {total} total':'필터 결과 {visible}개 / 전체 {total}개',
' · first 50 shown; exports contain all':' · 화면에는 앞의 50개를 표시하며 출력 파일에는 전체를 포함합니다',
'Supported code-risk patterns found. Inspect the origin and observed use; review the intended evaluation protocol.':'지원하는 코드 위험 패턴을 발견했습니다. 원인·사용 지점과 평가 목적을 함께 검토하세요.',
'No supported finding, with limited coverage. Unanalyzed scopes remain; this is not an all-clear.':'지원 범위에서 발견한 항목은 없지만 미분석 범위가 남아 있습니다. 전체에 문제가 없다는 뜻은 아닙니다.',
'No supported finding in the scoped analysis. This does not certify the whole program.':'지원 범위에서 발견한 항목이 없습니다. 프로그램 전체의 안전성을 인증하는 결과는 아닙니다.',
'Lexical search completed at the configured threshold. Similarity alone does not establish leakage or score inflation.':'설정한 기준의 어휘 겹침 검사를 완료했습니다. 유사도만으로 누출이나 점수 과장을 단정하지 않습니다.',
'INCOMPLETE: similarity budget reached. Additional overlaps may remain. Increase the budget with the CLI.':'미완료: 유사도 비교 한도에 도달했습니다. 추가 겹침이 남아 있을 수 있습니다. CLI에서 한도를 늘려 다시 검사하세요.',
'{count} comparisons / {budget} budget.':'유사도 비교 {count}회 / 한도 {budget}회.',
'Local analysis finished: {count} findings. Review the evidence and scope notes.':'로컬 검사 완료: {count}개 항목. 근거와 분석 범위 안내를 확인하세요.',
'Select an example or local files first.':'먼저 예제 또는 내 파일을 선택하세요.',
'Analysis cancelled.':'검사를 중단했습니다.',
'Analysis cancelled. No completion claim was made.':'검사를 중단했습니다. 완료된 검사 결과로 표시하지 않습니다.',
'Select 1–10 files.':'파일 1~10개를 선택하세요.',
'{name}: exceeds the 2 MB per-file browser limit.':'{name}: 브라우저의 파일당 2 MB 제한을 초과했습니다.',
'Files loaded locally. Scan when ready.':'기기 안에서 파일을 불러왔습니다. 준비되면 검사하세요.',
'Origin':'원인 지점','Observed use':'사용 지점',
'cell {cell} · line {line}':'셀 {cell} · {line}행','line {line}':'{line}행',
'row {row}':'{row}번째 행','source: {source}':'원본: {source}',
'label':'라벨','group':'그룹','Source: ':'출처: ',
'Preprocessing fitted before a holdout split':'홀드아웃 분할 전에 전처리를 학습함',
'Estimator fitted on held-out records':'분리해 둔 평가 데이터로 모델을 학습함',
'Prefitted features passed to cross-validation':'이미 학습한 특성을 교차검증에 사용함',
'Resampling applied before a holdout split':'홀드아웃 분할 전에 리샘플링을 수행함',
'Split raw data first; fit preprocessing on training only and transform the held-out set.':'원본 데이터를 먼저 분할하세요. 전처리는 학습 데이터에서만 fit하고 평가 데이터에는 transform만 적용하세요.',
'Keep validation/test records out of fit, fit_transform and fit_resample during evaluation.':'평가 중에는 개발·시험 데이터를 fit, fit_transform, fit_resample에 넣지 마세요.',
'Place fitted preprocessing inside a Pipeline so each fold learns it from that fold’s training records.':'전처리를 Pipeline 안에 넣어 각 폴드의 학습 데이터에서만 fit하도록 구성하세요.',
'Split first and resample training only, or use an imbalanced-learn Pipeline within cross-validation.':'먼저 분할하고 학습 데이터만 리샘플링하거나, 교차검증 안에서 imbalanced-learn Pipeline을 사용하세요.',
'A supported static data-flow pattern was observed. Review the intended evaluation protocol; this is not a proof of invalid model performance.':'지원하는 정적 데이터 흐름 패턴을 발견했습니다. 평가 목적을 검토해야 하며, 모델 성능이 잘못됐다는 증명은 아닙니다.',
'Static patterns require protocol review; no findings is not a leakage-free certification.':'정적 패턴은 평가 맥락을 검토해야 합니다. 발견 항목이 없더라도 누출이 없다는 인증은 아닙니다.',
'Function bodies, control flow, custom transformers/helpers and cross-file execution are not followed.':'함수 본문, 제어 흐름, 사용자 정의 변환기·도우미, 파일 간 실행은 추적하지 않습니다.',
'Notebook source order can differ from execution order; cells are never executed.':'노트북의 저장 순서와 실행 순서는 다를 수 있습니다. 검사 중 셀을 실행하지 않습니다.',
'No temporal, target-derived-feature, semantic or foundation-model contamination checks.':'시간 누출, 정답 파생 특성, 의미적 유사성, 기반 모델의 사전학습 오염은 검사하지 않습니다.',
'No findings does not establish a leakage-free evaluation.':'발견 항목이 없다는 사실만으로 누출 없는 평가가 입증되지는 않습니다.',
'No semantic, temporal, feature/target, pretraining or model-selection leakage detection.':'의미적·시간적 누출, 특성·정답 누출, 사전학습 오염, 모델 선택 과정의 누출은 탐지하지 않습니다.',
'Label conflicts may be valid when identical answers have different question context.':'같은 답안도 문항 맥락이 다르면 서로 다른 라벨이 타당할 수 있습니다.',
'Group overlap is meaningful only if the configured group is an isolation boundary.':'설정한 그룹을 실제로 분리해야 하는 평가에서만 그룹 겹침의 의미가 있습니다.',
'Token-set similarity ignores word order, token counts and multilingual semantics.':'토큰 집합 유사도는 어순·반복 횟수·다국어 의미를 반영하지 않습니다.',
'The same normalized text occurs in more than one split.':'정규화한 동일 텍스트가 여러 분할에 존재합니다.',
'Identical normalized text has different labels. Review task context before changing any label.':'정규화한 동일 텍스트의 라벨이 다릅니다. 라벨을 바꾸기 전에 과제 맥락을 검토하세요.',
'A configured isolation group occurs in multiple splits. Confirm that this group should be held out.':'분리 대상으로 설정한 그룹이 여러 분할에 존재합니다. 해당 그룹을 실제로 분리해야 하는지 확인하세요.',
'Token-set Jaccard meets the configured threshold; similarity alone does not establish leakage.':'토큰 집합의 자카드 유사도가 설정 기준 이상입니다. 유사도만으로 누출을 단정하지 않습니다.',
'Exact overlap':'정확 중복','Near overlap':'유사 문장 겹침','Group overlap':'그룹 겹침','Label conflict':'라벨 충돌','Label conflicts':'라벨 충돌',
'exact_overlap':'정확 중복','near_overlap':'유사 문장 겹침','group_overlap':'그룹 겹침','label_conflict':'라벨 충돌',
'Local · No API keys':'로컬 처리 · API 키 불필요',
'Trace overlapping text, shared groups and conflicting labels back to the exact rows that need review.':'텍스트 겹침, 공유 그룹, 라벨 충돌을 검토할 원본 행까지 추적합니다.',
'↓ Export audit JSON':'↓ 검사 JSON 내보내기','Split exposure':'분할별 겹침',
'Unique rows · union of overlap checks':'겹침 검사에 관련된 고유 행 기준',
'Evidence explorer':'검사 근거 탐색','Search text, label, group or row ID…':'텍스트·라벨·그룹·행 식별자 검색…',
'Finding type':'검사 종류','All checks':'모든 검사','Severity':'심각도','All severities':'모든 심각도',
'Error':'오류','Warning':'경고','error':'오류','warning':'경고',
'← Previous':'← 이전','Next →':'다음 →',
'What this audit can tell you':'이 검사 결과의 의미',
'These are observable overlaps and review candidates. Their meaning depends on your evaluation question. Row numbers count data records, excluding the CSV header.':'관찰된 겹침과 검토 후보를 보여줍니다. 의미는 평가 목적에 따라 달라집니다. 행 번호는 CSV 머리글을 제외한 데이터 레코드 기준입니다.',
'Reports contain the matched rows’ text. Exports preserve that evidence. No data is sent to a server.':'보고서와 출력 파일에는 해당 행의 원문이 포함됩니다. 입력 데이터를 서버로 보내지 않습니다.',
'Across all supplied splits':'입력한 전체 분할 기준','Rows with overlap':'겹침에 관련된 행','A row is counted once':'같은 행은 한 번만 계산',
'Exact / near findings':'정확 중복 / 유사 겹침','Exact clusters / near pairs':'정확 중복 묶음 / 유사 문장 쌍','Text clusters to review':'검토할 텍스트 묶음',
'● Findings require review':'● 검토할 항목이 있습니다','◐ Incomplete similarity search':'◐ 유사도 검사가 미완료됐습니다','✓ No findings within checked scope':'✓ 검사 범위 안에서 발견한 항목이 없습니다',
'Complete':'완료','INCOMPLETE':'미완료',
'No semantic or temporal checks were performed.':'의미적 유사성·시간 누출 검사는 수행하지 않았습니다.',
'Candidate budget reached. Unvisited candidates may contain additional overlaps. Increase the budget and rerun.':'비교 한도에 도달했습니다. 검사하지 못한 후보에 추가 겹침이 있을 수 있으므로 한도를 늘려 다시 실행하세요.',
'{state} lexical candidate search · {count} comparisons · Jaccard threshold {threshold}. {note}':'어휘 후보 검사 {state} · 비교 {count}회 · 자카드 기준 {threshold}. {note}',
'{overlap} / {rows} rows · {percent}%':'{rows}행 중 {overlap}행 · {percent}%',
'{name}: {percent} percent of rows have overlap':'{name}: 전체 행의 {percent}%가 겹침에 관련됨',
'{count} of {total} findings':'전체 {total}개 중 {count}개',
'{count} rows':'{count}행','Page {page} / {pages}':'{page} / {pages} 페이지',
'No findings match these filters.':'선택한 필터에 맞는 항목이 없습니다.',
'AST + scoped data-flow analysis for Python and Jupyter notebooks. Target code is never executed.':'Python·Jupyter 노트북의 AST와 지원 범위 안의 데이터 흐름을 분석합니다. 대상 코드는 실행하지 않습니다.',
'files scanned':'검사한 파일','findings to review':'검토할 항목','files with scope notes':'범위 안내가 있는 파일',
'Static patterns are review evidence. Function bodies, control flow, custom helpers and notebook execution order can fall outside analysis. No findings does not certify a leakage-free model.':'정적 패턴은 검토를 위한 근거입니다. 함수 본문·제어 흐름·사용자 정의 도우미·노트북 실행 순서는 분석 범위 밖일 수 있습니다. 발견 항목이 없더라도 누출 없는 모델이라는 인증은 아닙니다.',
'Coverage and abstentions':'분석 범위와 미분석 항목',
'No additional coverage notes.':'추가 분석 범위 안내가 없습니다.',
'No supported risk patterns found. Review the coverage notes below.':'지원하는 위험 패턴을 찾지 못했습니다. 아래의 분석 범위 안내를 확인하세요.',
'Primary documentation ↗':'공식 문서 ↗','statements':'개 문장',
'partial':'일부 범위 분석','findings':'검토 항목 있음','no_findings_in_scope':'지원 범위 내 발견 항목 없음',
'Fit receiver is not a supported imported sklearn/imblearn object; no inference made.':'fit 대상이 지원하는 sklearn/imblearn 객체로 확인되지 않아 판정하지 않았습니다.',
'Index/column projection is tracked conservatively; row-filter semantics are not resolved.':'인덱스·열 선택은 보수적으로 추적하며 행 필터의 의미는 판정하지 않습니다.',
'Tracked data passes through an unmodeled call; its output lineage is not inferred.':'추적 중인 데이터가 지원하지 않는 함수 호출을 거쳐 출력 흐름을 판정하지 않았습니다.',
'Attribute/subscript assignment is not analyzed; state tracking reset.':'속성·인덱스 대입을 분석하지 않아 상태 추적을 초기화했습니다.',
'Star imports are not resolved.':'별표(*) 가져오기의 이름을 판정하지 않습니다.',
'Function/class bodies are not analyzed; source-order analysis does not follow calls.':'함수·클래스 본문을 분석하지 않으며 저장 순서 분석으로 함수 호출 내부를 추적하지 않습니다.',
'Control-flow block is not analyzed; tracked data/object state is reset.':'제어 흐름 블록을 분석하지 않아 데이터·객체 상태 추적을 초기화했습니다.',
'Mutation is not analyzed; tracked state is reset.':'상태 변경을 분석하지 않아 추적을 초기화했습니다.',
'Cell-magic body skipped; tracked state reset.':'셀 매직 본문을 건너뛰고 상태 추적을 초기화했습니다.',
'Notebook magic/shell line skipped.':'노트북 매직·셸 명령 행을 건너뛰었습니다.',
'Execution counts are repeated/out of source order; source-order results may not match the executed notebook.':'실행 번호가 반복되거나 저장 순서와 다릅니다. 실제 실행 흐름과 검사 결과가 다를 수 있습니다.',
'Unresolved fit':'판정하지 못한 fit','unresolved_fit':'판정하지 못한 fit','projection':'선택·필터 범위','opaque_call':'미지원 함수 호출','mutation':'상태 변경','star_import':'별표 가져오기','scope_skipped':'미분석 함수·클래스','control_flow_skipped':'미분석 제어 흐름','unsupported_statement':'미지원 문장','cell_magic':'셀 매직','line_magic':'행 매직·셸 명령','parse_error':'구문 분석 실패','execution_order':'실행 순서','split_unpack':'분할 결과 대입',
'select 1–10 files':'파일 1~10개를 선택하세요',
'files require string name and text':'각 파일에는 문자열 형식의 파일명과 내용이 필요합니다',
'combined input exceeds 4 MB browser limit':'전체 입력이 브라우저의 4 MB 제한을 초과했습니다',
'code mode accepts .py or .ipynb':'코드 검사에는 .py 또는 .ipynb 파일을 사용하세요',
'dataset mode needs exactly two files: train, then test':'데이터 검사에는 학습·시험 순서로 파일 두 개가 필요합니다',
'dataset mode accepts CSV and JSONL':'데이터 검사에는 CSV 또는 JSONL 파일을 사용하세요',
'each browser input must contain 1–5,000 records':'각 브라우저 입력 파일에는 1~5,000개 레코드가 필요합니다',
'unknown browser mode':'지원하지 않는 브라우저 검사 종류입니다',
'supported file formats are .csv and .jsonl':'지원하는 데이터 파일 형식은 .csv와 .jsonl입니다',
'provide at least two nonempty splits':'비어 있지 않은 분할을 두 개 이상 입력하세요',
'code scan supports .py and .ipynb files':'코드 검사는 .py와 .ipynb 파일을 지원합니다',
'source exceeds 2 MB scan limit':'소스 코드가 2 MB 검사 제한을 초과했습니다',
'notebook exceeds 2 MB scan limit':'노트북이 2 MB 검사 제한을 초과했습니다',
'notebook must be an object with a cells array':'노트북에는 cells 배열이 필요합니다',
'each notebook cell must be an object':'노트북의 각 셀은 객체 형식이어야 합니다',
'code cell source must be a string or list of strings':'코드 셀의 source는 문자열 또는 문자열 목록이어야 합니다',
'scan requires 1–500 Python/notebook files':'Python·노트북 파일 1~500개를 선택하세요',
'each --split must be a unique NAME=PATH':'각 --split은 서로 다른 이름의 NAME=PATH 형식이어야 합니다',
'CODE SCAN: {files} files; {count} findings; {partial} files with scope notes':'코드 검사: {files}개 파일 · {count}개 항목 · 범위 안내가 있는 파일 {partial}개',
'Report: {path}':'보고서: {path}',
'Synthetic demonstration — findings intentionally planted.':'합성 예제 — 검사할 문제를 의도적으로 넣었습니다.',
'Proposed {train} train / {test} test rows; deleted 0.':'새 분할안: 학습 {train}행 / 시험 {test}행 · 삭제한 행 0개.',
'Post-split audit: {status}; {count} findings':'새 분할 검사: {status} · {count}개 항목',
'{status}: {count} findings / {rows} rows':'{status}: {rows}행 중 검토할 항목 {count}개',
'A proposal for a new evaluation, not a repair of a fixed benchmark. Inspect class balance and the evaluation question.':'고정 벤치마크를 수정한 결과가 아니라 새 평가를 위한 제안입니다. 클래스 비율과 평가 목적을 확인하세요.',
'review':'검토 필요','incomplete':'미완료','no_findings':'검사 범위 내 발견 항목 없음',
'Error detail: {detail}':'검사 오류 상세: {detail}',
'Unsupported language: {lang}':'지원하지 않는 언어: {lang}',
}

KO.update({
'Error detail:':'검사 오류 상세:',
'Start with a reproducible example':'재현 가능한 예제로 시작하세요',
'HTML report ↓':'HTML 보고서 ↓',
'EvalCheck — Find the line. Fix the split.':'EvalCheck — 원인 코드와 데이터 겹침 검사',
'EvalCheck · Notebook code evidence':'EvalCheck · 노트북 코드 검사 근거',
'Origin · {location}':'원인 지점 · {location}',
'Observed use · {location}':'사용 지점 · {location}',
'{path}: {kind} — {message}':'{path}: {kind} — {message}',
'{count} matching findings / {total} total · first 50 shown; exports contain all':'필터 결과 {count}개 / 전체 {total}개 · 앞의 50개 표시, 출력 파일에 전체 포함',
'EVALUATION INTEGRITY / v{version}':'평가 신뢰성 검사 / v{version}',
'{path} · {status} · {count} statements':'{path} · {status} · 문장 {count}개',
'{id}  /  {name}':'{id} / {name}',
'ERROR · {count} rows':'오류 · {count}행',
'WARNING · {count} rows':'경고 · {count}행',
'ERROR · {count} rows · Jaccard {similarity}':'오류 · {count}행 · 자카드 {similarity}',
'WARNING · {count} rows · Jaccard {similarity}':'경고 · {count}행 · 자카드 {similarity}',
})


def language(lang):
    if lang not in {'en','ko'}:raise ValueError(f'unsupported language: {lang}')
    return lang


def tr(message, lang='en', **values):
    language(lang)
    text=KO.get(message,message) if lang=='ko' else message
    # Literal replacement avoids interpreting braces in source/error text.
    for name,value in values.items():text=text.replace('{'+name+'}',str(value))
    return text


def localize_error(message, lang='en'):
    language(lang)
    if lang=='en':return message
    if message in KO:return KO[message]
    patterns=[
        (r'^(.*): missing column (.+)$',lambda m:f'{m[1]}: 필요한 열 {m[2]}이 없습니다'),
        (r'^(.*): text must be a nonempty string$',lambda m:f'{m[1]}: 텍스트는 비어 있지 않은 문자열이어야 합니다'),
        (r'^output directory must be empty: (.*)$',lambda m:f'출력 폴더는 비어 있어야 합니다: {m[1]}'),
        (r'^scan path does not exist: (.*)$',lambda m:f'검사할 경로가 없습니다: {m[1]}'),
        (r'^(.*): file exceeds 2 MB scan limit$',lambda m:f'{m[1]}: 파일이 2 MB 검사 제한을 초과했습니다'),
    ]
    for pattern,render in patterns:
        match=re.match(pattern,message)
        if match:return render(match)
    return tr('Error detail: {detail}',lang,detail=message)


class _HTMLLocale(HTMLParser):
    def __init__(self,lang):
        super().__init__(convert_charrefs=False);self.lang=lang;self.parts=[];self.skip=[]
    def handle_starttag(self,tag,attrs):
        out=[]
        for key,value in attrs:
            if key=='lang' and tag=='html':value=self.lang
            elif key in {'placeholder','aria-label','title','alt'} and value is not None:value=tr(value,self.lang)
            out.append(key if value is None else key+'="'+html.escape(value,quote=True)+'"')
        self.parts.append('<'+tag+(' '+' '.join(out) if out else '')+'>')
        if tag in {'script','style','pre','code','textarea'}:self.skip.append(tag)
    def handle_endtag(self,tag):
        self.parts.append('</'+tag+'>')
        if self.skip and self.skip[-1]==tag:self.skip.pop()
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        self.parts[-1]=self.parts[-1][:-1]+'/>'
    def handle_data(self,data):
        if self.skip:self.parts.append(data);return
        stripped=data.strip()
        if stripped and stripped in KO:
            prefix=data[:len(data)-len(data.lstrip())];suffix=data[len(data.rstrip()):]
            self.parts.append(prefix+html.escape(tr(stripped,self.lang))+suffix)
        else:self.parts.append(data)
    def handle_entityref(self,name):self.parts.append('&'+name+';')
    def handle_charref(self,name):self.parts.append('&#'+name+';')
    def handle_comment(self,data):self.parts.append('<!--'+data+'-->')
    def handle_decl(self,decl):self.parts.append('<!'+decl+'>')


def localize_html(page,lang='en'):
    language(lang)
    if lang=='en':return page
    parser=_HTMLLocale(lang);parser.feed(page);parser.close();return ''.join(parser.parts)


def locale_script(lang='en', *, interactive=False):
    import json
    from pathlib import Path
    language(lang)
    safe=lambda obj:json.dumps(obj,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return Path(__file__).with_name('locale-ui.js').read_text(encoding='utf-8').replace('__LOCALE_CATALOG__',safe(KO)).replace('__INITIAL_LANG__',safe(lang)).replace('__INTERACTIVE__','true' if interactive else 'false')
