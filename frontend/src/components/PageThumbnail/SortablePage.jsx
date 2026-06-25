import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { X, Maximize2, RotateCw } from "lucide-react";

import PdfJsThumbnail from "./PdfJsThumbnail";

export function SortablePage({ id, page, file, onRemove, isSelected, onToggleSelection, onEnlarge }) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.3 : 1,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`relative group bg-gray-700 rounded-lg shadow-md hover:shadow-xl transition-all border border-gray-600 overflow-hidden flex flex-col h-60 cursor-pointer
            ${isSelected ? 'ring-2 ring-purple-500 ring-offset-2 ring-offset-gray-900' : ''}`}
            onClick={(e) => {
                onToggleSelection(id, e.shiftKey, e.ctrlKey || e.metaKey);
            }}
        >
            {/* Selection Checkbox */}
            <div className={`absolute top-2 left-2 z-20 w-5 h-5 rounded border ${isSelected ? 'bg-purple-500 border-purple-500' : 'bg-gray-800/80 border-gray-500'} flex items-center justify-center`}>
                {isSelected && <div className="w-2 h-2 bg-white rounded-full" />}
            </div>

            {/* Drag Handle Overlay */}
            <div {...attributes} {...listeners} className="absolute inset-0 z-10" />

            {/* Delete Button */}
            <button
                onClick={(e) => { e.stopPropagation(); onRemove(id); }}
                className="absolute top-2 right-2 z-30 p-1 bg-red-500/80 hover:bg-red-600 rounded text-white opacity-0 group-hover:opacity-100 transition-opacity"
            >
                <X size={16} />
            </button>
            
            {/* Edit Button */}
            <button
                onClick={(e) => { e.stopPropagation(); onEnlarge(id); }}
                className="absolute bottom-12 right-2 z-30 p-1.5 bg-blue-500/80 hover:bg-blue-600 rounded text-white opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-xs font-medium backdrop-blur-sm"
            >
                <Maximize2 size={12} /> Edit
            </button>

            {/* Rotation Badge */}
            {page.rotation > 0 && (
                 <div className="absolute top-8 right-2 z-30 p-1 bg-gray-800/80 rounded-full text-white flex items-center justify-center backdrop-blur-sm">
                    <RotateCw size={14} />
                 </div>
            )}

            {/* Thumbnail */}
            <div className="flex-grow relative z-0">
                <PdfJsThumbnail
                    fileUrl={file?.url}
                    pageIndex={page.pageIndex}
                    rotation={page.rotation}
                    isDragging={isDragging}
                />
            </div>

            {/* Footer */}
            <div className="bg-gray-800 p-2 text-center border-t border-gray-700 h-8 flex items-center justify-center relative z-0">
                <p className="text-[10px] text-gray-400 truncate w-full px-2">
                    Pg {page.pageIndex + 1} • {file?.name}
                </p>
            </div>
        </div>
    );
}