import { useEffect, useState } from "react";

import { ArchaeologyPanel } from "./components/ArchaeologyPanel";
import { ExampleSelector } from "./components/ExampleSelector";
import { PhaseTimeline } from "./components/PhaseTimeline";
import { RefactorPlanPanel } from "./components/RefactorPlanPanel";
import { RiskPanel } from "./components/RiskPanel";
import { SourceViewerPanel } from "./components/SourceViewerPanel";
import { SynthesisPanel } from "./components/SynthesisPanel";
import { useJson } from "./lib/useJson";
import { useText } from "./lib/useText";
import type {
  ArchaeologyReport,
  ExamplesManifest,
  ProgressState,
  RefactorPlan,
  RiskAssessment,
  StageState,
} from "./types";

export default function App() {
  const { data: manifest } = useJson<ExamplesManifest>("examples.json", 10000);
  const examples = manifest?.examples ?? [];

  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  useEffect(() => {
    if (!selectedSlug && examples.length > 0) {
      setSelectedSlug(examples[0].slug);
    }
  }, [examples, selectedSlug]);

  const slug = selectedSlug ?? "legacy-app";
  const selected = examples.find((e) => e.slug === slug) ?? null;

  const { data: progress } = useJson<ProgressState>(`${slug}/progress_state.json`, 3000);
  const { data: archaeology } = useJson<ArchaeologyReport>(`${slug}/archaeology.json`, 5000);
  const { data: risk } = useJson<RiskAssessment>(`${slug}/risk_assessment.json`, 5000);
  const { data: plan } = useJson<RefactorPlan>(`${slug}/refactor_plan.json`, 5000);
  const synthesis = useText(`${slug}/synthesis_report.md`, 5000);

  const stagePhase = progress?.phases.find((p) => p.name === "stage_execution");
  const stageStates: StageState[] = stagePhase?.stages ?? [];

  return (
    <div className="app">
      <header>
        <h1>legacy-refactor-graph</h1>
        <p>
          A read-only dashboard over a legacy-modernization pipeline's own output — polls on its
          own, never writes anything back.
        </p>
        <ExampleSelector examples={examples} selected={selected} onSelect={setSelectedSlug} />
      </header>

      <PhaseTimeline progress={progress} />

      <div className="grid">
        <ArchaeologyPanel data={archaeology} />
        <RiskPanel data={risk} />
      </div>

      <RefactorPlanPanel plan={plan} stageStates={stageStates} />
      <SynthesisPanel text={synthesis} />
      <SourceViewerPanel target={slug} />
    </div>
  );
}
