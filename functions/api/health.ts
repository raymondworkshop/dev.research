import { healthResponse } from "../../workers/src/chat";

export const onRequestGet: PagesFunction = async () => healthResponse();
