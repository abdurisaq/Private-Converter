import React, { useEffect, useRef } from "react";
import * as pdfjs from "pdfjs-dist";

export const PdfJsModalRenderer = ({ fileUrl, pageIndex, rotation }) => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !fileUrl) return;

        let pdfDocument = null;
        let page = null;
        let destroyed = false;

        const renderPage = async () => {
            try {
                pdfDocument = await pdfjs.getDocument({ url: fileUrl }).promise;
                page = await pdfDocument.getPage(pageIndex + 1);
                if(destroyed) return;

                const viewport1x = page.getViewport({ scale: 1 });
                // Target width/height for display in modal
                const scale = Math.min(600 / viewport1x.width, 800 / viewport1x.height);
                const viewport = page.getViewport({ scale, rotation });

                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                await page.render({ canvasContext: context, viewport }).promise;
            } catch (e) { /* Console logs removed */ }
        };
        renderPage();
        return () => { destroyed = true; if(page) page.cleanup(); };
    }, [fileUrl, pageIndex, rotation]);

    return <canvas ref={canvasRef} className="shadow-2xl border border-gray-700" />;
};