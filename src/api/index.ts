import axios_ from "axios";



function getBackendProdUrl() {
    // @ts-ignore
    const getWebappBackendUrlFn = window['getWebAppBackendUrl'] || parent["getWebAppBackendUrl"];
      if (typeof getWebappBackendUrlFn === 'function') {
        return getWebappBackendUrlFn('');
    }
    return null
}

const baseURLClientVite = import.meta.env.VITE_BASE_URL;
let baseURLVite = import.meta.env.BASE_URL;
console.log(baseURLClientVite);

const backendProdBase = getBackendProdUrl();
const localBackendPort =  import.meta.env.VITE_API_PORT;
const localClientPort = import.meta.env.VITE_CLIENT_PORT;
console.log(localBackendPort);
console.log(localClientPort);

baseURLVite = baseURLVite.replace(localClientPort, localBackendPort);

const baseURL = backendProdBase != null ? backendProdBase: baseURLVite;

const axios = axios_.create({ baseURL });


axios.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      APIErrors.push(error.response);
      return Promise.reject(error);
    }
  );
  
  export const APIErrors: any[] = [];
  
  export default axios;
  export { baseURL, baseURLClientVite };

