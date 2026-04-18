import request from "./request";

export const get_department_role = () => {
  return request({
    url: "/role/department_role",
    method: "get",
  });
};

export const get_role_admin_meta = () => {
  return request({
    url: "/role/admin/meta",
    method: "get",
  });
};

export const list_admin_departments = () => {
  return request({
    url: "/role/admin/departments",
    method: "get",
  });
};

export const create_admin_department = (data) => {
  return request({
    url: "/role/admin/departments",
    method: "post",
    data,
  });
};

export const update_admin_department = (deptId, data) => {
  return request({
    url: `/role/admin/departments/${deptId}`,
    method: "put",
    data,
  });
};

export const delete_admin_department = (deptId) => {
  return request({
    url: `/role/admin/departments/${deptId}`,
    method: "delete",
  });
};

export const list_admin_roles = () => {
  return request({
    url: "/role/admin/roles",
    method: "get",
  });
};

export const create_admin_role = (data) => {
  return request({
    url: "/role/admin/roles",
    method: "post",
    data,
  });
};

export const update_admin_role = (roleId, data) => {
  return request({
    url: `/role/admin/roles/${roleId}`,
    method: "put",
    data,
  });
};

export const delete_admin_role = (roleId) => {
  return request({
    url: `/role/admin/roles/${roleId}`,
    method: "delete",
  });
};
