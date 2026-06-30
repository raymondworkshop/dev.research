import { handleChat } from "../../workers/src/chat";

export const onRequestPost: PagesFunction = async (context) => handleChat(context.request);
