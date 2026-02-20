import { BaseApi } from "@/api/base";

import { Counter } from "@/types/counter/schemas";

export class CounterApi extends BaseApi {
    prefix = "/api/counter";

    constructor() {
        super(import.meta.env.VITE_BACKEND_API_URL);
    }

    getUrl(id: string = "") {
        return `${this.prefix}/${id}`;
    }

    async step(counter: Counter) {
        return this.get<Counter>(this.getUrl(""), { step: counter.step, current: counter.current });
    }
}
