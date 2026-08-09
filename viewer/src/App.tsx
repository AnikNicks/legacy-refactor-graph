import { ArchaeologyPanel } from "./components/ArchaeologyPanel";
import { PhaseTimeline } from "./components/PhaseTimeline";
import { RefactorPlanPanel } from "./components/RefactorPlanPanel";
import { RiskPanel } from "./components/RiskPanel";
import { SynthesisPanel } from "./components/SynthesisPanel";
import { useJson } from "./lib/useJson";
import { useText } from "./lib/useText";
import type { ArchaeologyReport, ProgressState, RefactorPlan, RiskAssessment, StageState } from "./types";

export default function App() {
  const { data: progress } = useJson<ProgressState>("progress_state.json", 3000);
  const { data: archaeology } = useJson<ArchaeologyReport>("archaeology.json", 5000);
  const { data: risk } = useJson<RiskAssessment>("risk_assessment.json", 5000);
  const { data: plan } = useJson<RefactorPlan>("refactor_plan.json", 5000);
  const synthesis = useText("synthesis_report.md", 5000);

  const stagePhase = progress?.phases.find((p) => p.name === "stage_execution");
  const stageStates: StageState[] = stagePhase?.stages ?? [];

  return (
    <div className="app">
      <header>
        <h1>legacy-refactor-graph</h1>
        <p>Read-only dashboard over output/*.json — polls on its own, never writes anything.</p>
      </header>

      <PhaseTimeline progress={progress} />

      <div className="grid">
        <ArchaeologyPanel data={archaeology} />
        <RiskPanel data={risk} />
      </div>

      <RefactorPlanPanel plan={plan} stageStates={stageStates} />
      <SynthesisPanel text={synthesis} />
    </div>
  );
}
