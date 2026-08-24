export type SectionName =
  | 'model'
  | 'mispricing'
  | 'measurement'
  | 'discrimination'
  | 'cases'
  | 'data'

export default function SectionMark({
  name,
  className = '',
}: {
  name: SectionName
  className?: string
}) {
  return (
    <span
      className={`section-mark ${className}`.trim()}
      data-mark={name}
      aria-hidden="true"
      style={{
        WebkitMaskImage: `url(/marks/${name}.svg)`,
        maskImage: `url(/marks/${name}.svg)`,
      }}
    />
  )
}
