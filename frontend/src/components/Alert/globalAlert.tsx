import { Alert } from "antd";

interface Props {
  alert: {
    open: boolean;
    type: "success" | "error" | "warning" | "info";
    message: string;
  };
  onClose: () => void;
}

export const GlobalAlert: React.FC<Props> = ({ alert, onClose }) => {
  if (!alert.open) return null;

  return (
    <div style={{ position: "fixed", top: 16, right: 16, zIndex: 1000 }}>
      <Alert
        message={alert.message}
        type={alert.type}
        showIcon
        closable
        onClose={onClose}
      />
    </div>
  );
};
