import { v4 as uuidv4 } from "uuid";

// --- HELPER: Backend Mock ---
export const mockUploadToBackend = async (file) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return `server_file_${uuidv4().slice(0, 8)}`;
};

//the idea behind moving multiple pages at a time
export const arrayMoveMultiple = (array, idsToMove, activeId, overId) => {
    const activeIndex = array.findIndex(i => i.id === activeId);
    const overIndex = array.findIndex(i => i.id === overId);
    const isMovingDown = activeIndex < overIndex;

    const movingItems = array.filter(item => idsToMove.includes(item.id));
    const remainder = array.filter(item => !idsToMove.includes(item.id));

    let insertAtIndex = remainder.findIndex(item => item.id === overId);

    if (insertAtIndex === -1) {
        return [...remainder, ...movingItems];
    }

    if (isMovingDown) {
        insertAtIndex += 1;
    }

    return [
        ...remainder.slice(0, insertAtIndex),
        ...movingItems,
        ...remainder.slice(insertAtIndex)
    ];
};