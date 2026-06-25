import PdfJsThumbnail from "./PdfJsThumbnail";

export const DragOverlayContent = ({ ids, pages, files }) => {
    const count = ids.length;
    const primaryId = ids[0];
    const page = pages.find(p => p.id === primaryId);
    const file = files[page?.fileId];

    if (!page || !file) return null;

    return (
        <div className="relative">
            {/* Stack Effect for multiple items */}
            {count > 1 && (
                <>
                    <div className="absolute top-2 left-2 w-full h-full bg-gray-700 rounded-lg border border-gray-600 shadow-sm z-0 transform rotate-3" />
                    <div className="absolute top-1 left-1 w-full h-full bg-gray-700 rounded-lg border border-gray-600 shadow-sm z-10 transform -rotate-2" />
                </>
            )}

            {/* Main Card */}
            <div className={`relative z-20 w-40 h-52 bg-gray-800 rounded-lg shadow-2xl border border-purple-500 flex flex-col overflow-hidden`}>
                <div className="flex-grow">
                    <PdfJsThumbnail
                        fileUrl={file.url}
                        pageIndex={page.pageIndex}
                        rotation={page.rotation}
                        isOverlay={true}
                    />
                </div>

                {/* Badge for Count */}
                {count > 1 && (
                    <div className="absolute -top-3 -right-3 bg-purple-600 text-white font-bold rounded-full w-8 h-8 flex items-center justify-center shadow-lg border-2 border-gray-900 z-50">
                        {count}
                    </div>
                )}
            </div>
        </div>
    );
};