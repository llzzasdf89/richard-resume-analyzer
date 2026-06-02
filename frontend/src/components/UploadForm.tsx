import { useState, useRef } from "react";

interface UploadFormProps {
  onSubmit: (resume: File, jd: string) => void;
  isLoading: boolean;
}

export default function UploadForm({ onSubmit, isLoading }: UploadFormProps) {
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!resume || !jd.trim() || isLoading) return;
    onSubmit(resume, jd);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* PDF 上传 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          上传简历（PDF）
        </label>
        <div
          onClick={() => fileRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
            transition-colors
            ${
              resume
                ? "border-blue-400 bg-blue-50"
                : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
            }
          `}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => setResume(e.target.files?.[0] ?? null)}
          />
          {resume ? (
            <div className="space-y-1">
              <div className="text-2xl">📄</div>
              <p className="text-sm font-medium text-blue-600">{resume.name}</p>
              <p className="text-xs text-gray-400">点击重新选择</p>
            </div>
          ) : (
            <div className="space-y-1">
              <div className="text-2xl">⬆️</div>
              <p className="text-sm text-gray-500">点击上传 PDF 简历</p>
              <p className="text-xs text-gray-400">支持 PDF 格式</p>
            </div>
          )}
        </div>
      </div>

      {/* JD 输入 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          目标职位描述（JD）
        </label>
        <textarea
          value={jd}
          onChange={(e) => setJd(e.target.value)}
          placeholder="粘贴招聘 JD 全文..."
          rows={8}
          disabled={isLoading}
          className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            disabled:bg-gray-50 disabled:cursor-not-allowed
            resize-none placeholder-gray-400"
        />
      </div>

      <button
        type="submit"
        disabled={!resume || !jd.trim() || isLoading}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium text-sm
          hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed
          transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            分析中...
          </>
        ) : (
          "开始分析"
        )}
      </button>
    </form>
  );
}
