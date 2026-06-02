interface SkillTagsProps {
  skills: string[];
  variant: "matched" | "missing" | "nice";
}

const variantStyles = {
  matched: "bg-green-100 text-green-700 border-green-200",
  missing: "bg-red-100 text-red-700 border-red-200",
  nice: "bg-blue-100 text-blue-700 border-blue-200",
};

export default function SkillTags({ skills, variant }: SkillTagsProps) {
  if (!skills.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {skills.map((skill) => (
        <span
          key={skill}
          className={`text-xs px-2.5 py-1 rounded-full border font-medium ${variantStyles[variant]}`}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}
