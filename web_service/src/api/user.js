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
