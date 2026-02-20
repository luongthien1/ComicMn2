import { AlertContext } from "@/components/Alert/alertContext";
import React from "react";
import { Button } from "antd/es/radio";
import { CounterApi } from "@/api/base/example/count";

interface State {
    count: number;
}

export default class Home extends React.Component<{}, State> {
    declare context: React.ContextType<typeof AlertContext>;
    static contextType = AlertContext;

    state: State = {
        count: 0
    };

    render() {
        return (
            <div>
                <h1>Welcome to the Home Page</h1>
                <p>This is the main landing page of the application.</p>
                <p>Current count: {this.state.count}</p>
                <Button onClick={() => {
                    const api = new CounterApi()
                    api.step({ current: this.state.count, step: 1 })
                        .then(res => {
                            this.setState({ count: res.current });
                            this.context!.show("info", "Count updated successfully!");
                        }).catch(err => {
                            this.context!.show("error", "Failed to update count: " + err.message);
                        });
                }}>Increment Count</Button>
            </div>
        );
    }
}
