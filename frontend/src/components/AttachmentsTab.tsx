import { FileText, File, Image } from 'lucide-react';
import type { Attachment } from '../types';

interface AttachmentsTabProps {
  attachments: Attachment[];
}

const FILE_ICONS: Record<string, typeof FileText> = {
  pdf: FileText,
  doc: File,
  docx: File,
  image: Image,
  jpg: Image,
  png: Image,
};

export function AttachmentsTab({ attachments }: AttachmentsTabProps) {
  if (!attachments || attachments.length === 0) return <div className="detail-empty">No attachments found</div>;

  return (
    <div className="attachments-tab">
      {attachments.map((att) => {
        const IconComponent = FILE_ICONS[att.file_type] || FileText;
        return (
          <div key={att.attachment_id} className="attachment-row">
            <IconComponent size={18} className="attachment-icon" />
            <div className="attachment-info">
              <span className="attachment-name">{att.file_name}</span>
              <span className="attachment-note">{att.short_note}</span>
            </div>
            <div className="attachment-meta">
              <span className="attachment-date">{att.upload_date}</span>
              <span className="attachment-type">{att.file_type.toUpperCase()}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
