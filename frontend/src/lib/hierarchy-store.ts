import { create } from "zustand";
import { persist } from "zustand/middleware";

interface HierarchyContext {
  organizationId: string | null;
  organizationName: string | null;
  unitId: string | null;
  unitName: string | null;
  departmentId: string | null;
  departmentName: string | null;
  projectId: string | null;
  projectName: string | null;
  workspaceId: string | null;
  workspaceName: string | null;
}

interface HierarchyState extends HierarchyContext {
  setOrganization: (id: string, name: string) => void;
  setUnit: (id: string, name: string) => void;
  setDepartment: (id: string, name: string) => void;
  setProject: (id: string, name: string) => void;
  setWorkspace: (id: string, name: string) => void;
  clearBelow: (level: "organization" | "unit" | "department" | "project") => void;
  reset: () => void;
}

const initialState: HierarchyContext = {
  organizationId: null,
  organizationName: null,
  unitId: null,
  unitName: null,
  departmentId: null,
  departmentName: null,
  projectId: null,
  projectName: null,
  workspaceId: null,
  workspaceName: null,
};

export const useHierarchyStore = create<HierarchyState>()(
  persist(
    (set) => ({
      ...initialState,
      setOrganization: (id, name) =>
        set({
          organizationId: id,
          organizationName: name,
          unitId: null,
          unitName: null,
          departmentId: null,
          departmentName: null,
          projectId: null,
          projectName: null,
          workspaceId: null,
          workspaceName: null,
        }),
      setUnit: (id, name) =>
        set({
          unitId: id,
          unitName: name,
          departmentId: null,
          departmentName: null,
          projectId: null,
          projectName: null,
          workspaceId: null,
          workspaceName: null,
        }),
      setDepartment: (id, name) =>
        set({
          departmentId: id,
          departmentName: name,
          projectId: null,
          projectName: null,
          workspaceId: null,
          workspaceName: null,
        }),
      setProject: (id, name) =>
        set({
          projectId: id,
          projectName: name,
          workspaceId: null,
          workspaceName: null,
        }),
      setWorkspace: (id, name) =>
        set({
          workspaceId: id,
          workspaceName: name,
        }),
      clearBelow: (level) => {
        const clears: Record<string, Partial<HierarchyContext>> = {
          organization: {
            unitId: null,
            unitName: null,
            departmentId: null,
            departmentName: null,
            projectId: null,
            projectName: null,
            workspaceId: null,
            workspaceName: null,
          },
          unit: {
            departmentId: null,
            departmentName: null,
            projectId: null,
            projectName: null,
            workspaceId: null,
            workspaceName: null,
          },
          department: {
            projectId: null,
            projectName: null,
            workspaceId: null,
            workspaceName: null,
          },
          project: {
            workspaceId: null,
            workspaceName: null,
          },
        };
        set(clears[level] ?? {});
      },
      reset: () => set(initialState),
    }),
    { name: "hierarchy-storage" }
  )
);
