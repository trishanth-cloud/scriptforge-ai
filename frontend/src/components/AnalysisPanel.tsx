"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Tag,
  ListOrdered,
  Loader2,
} from "lucide-react";
import { AnalysisResult, ExecutionPlan, TaskStatus } from "@/lib/types";

interface AnalysisPanelProps {
  analysis: AnalysisResult | undefined;
  executionPlan: ExecutionPlan | undefined;
  status: TaskStatus;
}

function Section({
  title,
  icon,
  children,
  defaultOpen = true,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-surface-border/50 last:border-b-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full px-4 py-3 text-left hover:bg-surface-light/20 transition-colors"
      >
        {open ? (
          <ChevronDown className="w-4 h-4 text-foreground/40" />
        ) : (
          <ChevronRight className="w-4 h-4 text-foreground/40" />
        )}
        <span className="text-foreground/50">{icon}</span>
        <span className="text-sm font-medium text-foreground/80">{title}</span>
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

function Badge({ children, color = "default" }: { children: React.ReactNode; color?: string }) {
  const colors: Record<string, string> = {
    default: "bg-surface-lighter text-foreground/70",
    primary: "bg-primary/15 text-primary-light",
    green: "bg-accent-green/15 text-accent-green",
    yellow: "bg-accent-yellow/15 text-accent-yellow",
    red: "bg-accent-red/15 text-accent-red",
    blue: "bg-accent-blue/15 text-accent-blue",
  };
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        colors[color] || colors.default
      }`}
    >
      {children}
    </span>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value > 0.7 ? "bg-accent-green" : value > 0.4 ? "bg-accent-yellow" : "bg-accent-red";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-surface-lighter rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-foreground/60">{pct}%</span>
    </div>
  );
}

function SkeletonBlock() {
  return (
    <div className="space-y-3 p-4">
      <div className="h-4 bg-surface-lighter rounded animate-pulse w-3/4" />
      <div className="h-3 bg-surface-lighter rounded animate-pulse w-full" />
      <div className="h-3 bg-surface-lighter rounded animate-pulse w-5/6" />
      <div className="h-3 bg-surface-lighter rounded animate-pulse w-2/3" />
    </div>
  );
}

export default function AnalysisPanel({
  analysis,
  executionPlan,
  status,
}: AnalysisPanelProps) {
  const isLoading =
    status === TaskStatus.ANALYZING ||
    status === TaskStatus.PLANNING ||
    status === TaskStatus.GENERATING ||
    status === TaskStatus.VALIDATING;

  if (!analysis && !isLoading) return null;

  return (
    <div className="bg-surface rounded-xl border border-surface-border overflow-hidden animate-fade-in">
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <h3 className="text-sm font-semibold text-foreground/90">
          AI Analysis
        </h3>
        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-primary">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span className="capitalize">{status.replace(/_/g, " ")}...</span>
          </div>
        )}
      </div>

      {!analysis ? (
        <SkeletonBlock />
      ) : (
        <>
          {/* Summary */}
          <Section title="Summary" icon={<ListOrdered className="w-4 h-4" />}>
            <p className="text-sm text-foreground/70 leading-relaxed">
              {analysis.summary}
            </p>
          </Section>

          {/* Extracted Instructions */}
          {analysis.extracted_instructions.length > 0 && (
            <Section
              title="Extracted Instructions"
              icon={<CheckCircle2 className="w-4 h-4" />}
            >
              <ol className="space-y-2">
                {analysis.extracted_instructions.map((inst, i) => (
                  <li key={`instruction-${i}`} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-accent-green shrink-0 mt-0.5" />
                    <span className="text-foreground/70">{inst}</span>
                  </li>
                ))}
              </ol>
            </Section>
          )}

          {/* Detected Variables */}
          {analysis.detected_variables.length > 0 && (
            <Section
              title="Detected Variables"
              icon={<Tag className="w-4 h-4" />}
            >
              <div className="flex flex-wrap gap-2">
                {analysis.detected_variables.map((v, i) => (
                  <Badge key={`var-${i}-${v}`} color="blue">
                    {v}
                  </Badge>
                ))}
              </div>
            </Section>
          )}

          {/* Dependencies */}
          {analysis.dependencies.length > 0 && (
            <Section
              title="Dependencies"
              icon={<Tag className="w-4 h-4" />}
              defaultOpen={false}
            >
              <div className="flex flex-wrap gap-2">
                {analysis.dependencies.map((d, i) => (
                  <Badge key={`dep-${i}-${d}`} color="primary">
                    {d}
                  </Badge>
                ))}
              </div>
            </Section>
          )}

          {/* Ambiguities */}
          {analysis.ambiguities.length > 0 && (
            <Section
              title="Ambiguities & Warnings"
              icon={<AlertTriangle className="w-4 h-4" />}
              defaultOpen={false}
            >
              <ul className="space-y-2">
                {analysis.ambiguities.map((a, i) => (
                  <li key={`ambiguity-${i}`} className="flex items-start gap-2 text-sm">
                    <AlertTriangle className="w-4 h-4 text-accent-yellow shrink-0 mt-0.5" />
                    <span className="text-foreground/70">{a}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {/* Metadata */}
          <Section
            title="Classification"
            icon={<Tag className="w-4 h-4" />}
          >
            <div className="space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge color="primary">{analysis.task_type}</Badge>
                <Badge color="green">{analysis.recommended_language}</Badge>
              </div>
              <div>
                <p className="text-xs text-foreground/50 mb-1.5">Confidence</p>
                <ConfidenceBar value={analysis.confidence} />
              </div>
              {analysis.explanation && (
                <p className="text-xs text-foreground/50 leading-relaxed">
                  {analysis.explanation}
                </p>
              )}
            </div>
          </Section>

          {/* Execution Plan */}
          {executionPlan && (
            <Section
              title="Execution Plan"
              icon={<ListOrdered className="w-4 h-4" />}
            >
              <div className="space-y-3">
                <p className="text-sm text-foreground/70">
                  {executionPlan.description}
                </p>
                <div className="flex gap-2 flex-wrap">
                  <Badge color="primary">
                    Complexity: {executionPlan.estimated_complexity}
                  </Badge>
                  <Badge color="blue">{executionPlan.language}</Badge>
                </div>
                <ol className="space-y-2 mt-2">
                  {executionPlan.steps.map((step, idx) => {
                    const stepNum =
                      typeof step === "object" && step !== null && "step_number" in step
                        ? step.step_number
                        : idx + 1;
                    const desc =
                      typeof step === "object" && step !== null && "description" in step
                        ? step.description
                        : String(step);
                    return (
                      <li
                        key={`plan-step-${idx}-${stepNum}`}
                        className="flex items-start gap-2 text-sm"
                      >
                        <span className="shrink-0 w-5 h-5 rounded-full bg-primary/15 text-primary text-xs flex items-center justify-center font-medium">
                          {stepNum}
                        </span>
                        <span className="text-foreground/70">{desc}</span>
                      </li>
                    );
                  })}
                </ol>
                {executionPlan.warnings.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {executionPlan.warnings.map((w, i) => (
                      <div
                        key={`plan-warning-${i}`}
                        className="flex items-start gap-2 text-xs text-accent-yellow"
                      >
                        <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}
