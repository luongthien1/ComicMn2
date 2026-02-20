import { createContext, useContext, useState } from "react";
import { GlobalAlert } from "./globalAlert";

export type AlertType = "success" | "error" | "warning" | "info";

interface AlertState {
  open: boolean;
  type: AlertType;
  message: string;
}

interface AlertContextValue {
  show: (type: AlertType, message: string) => void;
  hide: () => void;
}

export const AlertContext = createContext<AlertContextValue | null>(null);

export const AlertProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [alert, setAlert] = useState<AlertState>({
    open: false,
    type: "info",
    message: "",
  });

  const show = (type: AlertType, message: string) => {
    setAlert({ open: true, type, message });
  };

  const hide = () => {
    setAlert((a) => ({ ...a, open: false }));
  };

  return (
    <AlertContext.Provider value={{ show, hide }}>
      {children}
      <GlobalAlert alert={alert} onClose={hide} />
    </AlertContext.Provider>
  );
};

export const useAlert = () => {
  const ctx = useContext(AlertContext);
  if (!ctx) throw new Error("useAlert must be used inside AlertProvider");
  return ctx;
};
