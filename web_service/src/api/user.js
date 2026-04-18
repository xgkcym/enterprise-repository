import request from "./request";

export const user_login = (data) => {
  return request({
    url: "/user/login",
    method: "post",
    data,
  });
};

export const get_user_profile = () => {
  return request({
    url: "/user/profile",
    method: "get",
  });
};

export const update_user_profile = (data) => {
  return request({
    url: "/user/profile",
    method: "put",
    data,
  });
};

export const get_admin_user_meta = () => {
  return request({
    url: "/user/admin/meta",
    method: "get",
  });
};

export const list_admin_users = () => {
  return request({
    url: "/user/admin/users",
    method: "get",
  });
};

export const create_admin_user = (data) => {
  return request({
    url: "/user/admin/users",
    method: "post",
    data,
  });
};

export const update_admin_user = (userId, data) => {
  return request({
    url: `/user/admin/users/${userId}`,
    method: "put",
    data,
  });
};
