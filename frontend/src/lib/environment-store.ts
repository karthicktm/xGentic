import { create } from "zustand";
import { persist } from "zustand/middleware";

interface EnvironmentState {
  environmentId: string | null;
  environmentName: string | null;
  environmentType: string | null;
  setEnvironment: (id: string, name: string, type: string) => void;
  clearEnvironment: () => void;
}

export const useEnvironmentStore = create<EnvironmentState>()(
  persist(
    (set) => ({
      environmentId: null,
      environmentName: null,
      environmentType: null,
      setEnvironment: (id, name, type) =>
        set({ environmentId: id, environmentName: name, environmentType: type }),
      clearEnvironment: () =>
        set({ environmentId: null, environmentName: null, environmentType: null }),
    }),
    { name: "environment-storage" }
  )
);
