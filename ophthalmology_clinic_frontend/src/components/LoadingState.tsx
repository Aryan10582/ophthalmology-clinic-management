export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="rounded border border-clinic-line bg-white px-4 py-5 text-sm text-clinic-muted shadow-soft">
      {label}...
    </div>
  );
}
