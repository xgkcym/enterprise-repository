import request from "./request";

export const upload_file = (data) => {
  return request({
    url: "/file/upload",
    method: "post",
    data,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const get_upload_departments = () => {
  return request({
    url: "/file/departments",
    method: "get",
  });
};

export const get_file = () => {
  return request({
    url: "/file/query_file",
    method: "get",
  });
};

export const download_file = async (downloadUrl, fileName) => {
  const blob = await request({
    url: downloadUrl,
    method: "get",
    responseType: "blob",
  });

  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = fileName || "download";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(objectUrl);
};
