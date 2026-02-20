import React from "react";
import {
    Modal,
    Form,
    Input,
    Checkbox,
    Button,
    Space,
    Select,
    Divider,
    List,
    Dropdown
} from "antd";
import { Project, PipelineNode } from "@/types/schemas";
import { MOCK_MODELS } from "@/constants/mock_data";

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSave: (projectData: Partial<Project>) => void;
    initialData?: Project;
    title: string;
}

interface State {
    formData: Partial<Project>;
}

export default class ProjectFormModal extends React.Component<Props, State> {
    state: State = {
        formData: {
            name: "",
            description: "",
            status: "Active",
            datasetIds: [],
            modelIds: [],
            pipeline: []
        }
    };

    componentDidUpdate(prevProps: Props) {
        if (this.props.isOpen && !prevProps.isOpen) {
            this.setState({
                formData: this.props.initialData
                    ? { ...this.props.initialData }
                    : {
                        name: "",
                        description: "",
                        status: "Active",
                        datasetIds: [],
                        modelIds: [],
                        pipeline: []
                    }
            });
        }
    }


    addPipelineStep = () => {
        const newNode: PipelineNode = {
            id: `node-${Date.now()}`,
            label: "New Step",
            type: "ETL",
            status: "pending",
            description: ""
        };

        this.setState(prev => ({
            formData: {
                ...prev.formData,
                pipeline: [...(prev.formData.pipeline || []), newNode]
            }
        }));
    };

    updatePipelineStep = (
        index: number,
        field: keyof PipelineNode,
        value: string
    ) => {
        const pipeline = [...(this.state.formData.pipeline || [])];
        pipeline[index] = { ...pipeline[index], [field]: value };

        this.setState({
            formData: { ...this.state.formData, pipeline }
        });
    };

    removePipelineStep = (index: number) => {
        const pipeline = (this.state.formData.pipeline || []).filter(
            (_, i) => i !== index
        );

        this.setState({
            formData: { ...this.state.formData, pipeline }
        });
    };

    /* ---------------- Save ---------------- */

    handleSave = () => {
        if (!this.state.formData.name) return;
        this.props.onSave(this.state.formData);
    };

    /* ---------------- Render ---------------- */

    render() {
        const { isOpen, onClose, title, initialData } = this.props;
        const { formData } = this.state;

        return (
            <Modal
                open={isOpen}
                title={title}
                onCancel={onClose}
                width={900}
                footer={null}
                destroyOnClose
            >
                <Form layout="vertical">
                    <Form.Item label="Project Name" required>
                        <Input
                            value={formData.name}
                            onChange={e =>
                                this.setState({
                                    formData: { ...formData, name: e.target.value }
                                })
                            }
                        />
                    </Form.Item>

                    <Form.Item label="Description">
                        <Input
                            value={formData.description}
                            onChange={e =>
                                this.setState({
                                    formData: { ...formData, description: e.target.value }
                                })
                            }
                        />
                    </Form.Item>

                    <Divider />

                    <Form.Item label="Associate Datasets">
                        <Dropdown ></Dropdown>
                        <Checkbox.Group
                            value={formData.datasetIds}
                            options={[].map(ds => ({ //Datasets to be fetched from backend
                                label: ds.name,
                                value: ds.id
                            }))}
                            onChange={vals =>
                                this.setState({
                                    formData: { ...formData, datasetIds: vals as string[] }
                                })
                            }
                        />
                    </Form.Item>

                    <Form.Item label="Associate Models">
                        <Checkbox.Group
                            value={formData.modelIds}
                            options={MOCK_MODELS.map(m => ({
                                label: m.name,
                                value: m.id
                            }))}
                            onChange={vals =>
                                this.setState({
                                    formData: { ...formData, modelIds: vals as string[] }
                                })
                            }
                        />
                    </Form.Item>

                    <Divider />

                    <Space
                        style={{ width: "100%", justifyContent: "space-between" }}
                    >
                        <strong>Pipeline Steps</strong>
                        <Button type="dashed" onClick={this.addPipelineStep}>
                            + Add Step
                        </Button>
                    </Space>

                    <List
                        style={{ marginTop: 12 }}
                        dataSource={formData.pipeline}
                        locale={{ emptyText: "No pipeline steps yet" }}
                        renderItem={(node, idx) => (
                            <List.Item
                                actions={[
                                    <Button
                                        danger
                                        type="link"
                                        onClick={() => this.removePipelineStep(idx)}
                                    >
                                        Remove
                                    </Button>
                                ]}
                            >
                                <Space style={{ width: "100%" }}>
                                    <Input
                                        placeholder="Step name"
                                        value={node.label}
                                        onChange={e =>
                                            this.updatePipelineStep(
                                                idx,
                                                "label",
                                                e.target.value
                                            )
                                        }
                                    />

                                    <Select
                                        value={node.type}
                                        style={{ width: 160 }}
                                        onChange={v =>
                                            this.updatePipelineStep(idx, "type", v)
                                        }
                                        options={[
                                            { value: "Dataset", label: "Dataset" },
                                            { value: "ETL", label: "Preprocessing" },
                                            { value: "Model", label: "Training" },
                                            { value: "QA", label: "Validation" },
                                            { value: "Deploy", label: "Deployment" }
                                        ]}
                                    />

                                    <Input
                                        placeholder="Description"
                                        value={node.description}
                                        onChange={e =>
                                            this.updatePipelineStep(
                                                idx,
                                                "description",
                                                e.target.value
                                            )
                                        }
                                    />
                                </Space>
                            </List.Item>
                        )}
                    />

                    <Divider />

                    <Space style={{ width: "100%", justifyContent: "end" }}>
                        <Button onClick={onClose}>Cancel</Button>
                        <Button
                            type="primary"
                            disabled={!formData.name}
                            onClick={() => {
                                const { formData } = this.state;
                                if (!formData?.name) return;
                                this.props.onSave(formData);
                            }}
                        >
                            {initialData ? "Update Project" : "Create Project"}
                        </Button>
                    </Space>
                </Form>
            </Modal>
        );
    }
}
