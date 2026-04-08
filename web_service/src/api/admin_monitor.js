import request from "./request";

export const get_agent_monitor_overview = () => {
  return request({
    url: "/agent/admin/monitor/overview",
    method: "get",
  });
};

export const get_agent_monitor_runs = (params = {}) => {
  return request({
    url: "/agent/admin/monitor/runs",
    method: "get",
    params,
  });
};
