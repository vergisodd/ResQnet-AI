export function SkeletonPanel() {
  return (
    <div
      className="rounded-ui border border-cyan/10 bg-white/[0.04] p-5"
      aria-label="Loading dashboard preview"
      role="status"
    >
      <div className="h-3 w-2/3 animate-pulse rounded-full bg-white/10" />
      <div className="mt-4 grid gap-3">
        <div className="h-16 animate-pulse rounded-ui bg-white/10" />
        <div className="h-16 animate-pulse rounded-ui bg-white/10" />
        <div className="h-16 animate-pulse rounded-ui bg-white/10" />
      </div>
    </div>
  );
}
