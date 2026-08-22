import Image from 'next/image'

export type SectionName =
  | 'model'
  | 'mispricing'
  | 'measurement'
  | 'evidence'
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
    <Image
      className={`section-mark ${className}`.trim()}
      src={`/marks/${name}.svg`}
      width={28}
      height={28}
      alt=""
      aria-hidden="true"
      unoptimized
    />
  )
}
