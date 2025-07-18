// src/config.js

import { UserInfo, claim } from "@/models";


declare global {
    interface Window {
        appConfig?: Record<string, any>;
        activeUserId?: string;
        userInfo?: UserInfo;
    }
}

export let API_URL: string | null = null;
export let USER_ID: string | null = null;
export let USER_INFO: UserInfo | null = null;

export let config = {
    API_URL: "https://backendaigovnieuw-htgqhzbxhbachcgb.westeurope-01.azurewebsites.net/api",
    ENABLE_AUTH: false,
};

export function setApiUrl(url: string | null) {
    if (url) {
        API_URL = url.includes('/api') ? url : `${url}/api`;
    }
}
export function setUserInfoGlobal(userInfo: UserInfo | null) {
    if (userInfo) {
        USER_ID = userInfo.user_id || null;
        USER_INFO = userInfo;
    }
}
export function setEnvData(configData: Record<string, any>) {
    if (configData) {
        config.API_URL = configData.API_URL || "";
        config.ENABLE_AUTH = configData.ENABLE_AUTH || false;
    }
}

export function getConfigData() {
    if (!config.API_URL || !config.ENABLE_AUTH) {
        // Check if window.appConfig exists
        if (window.appConfig) {
            setEnvData(window.appConfig);
        }
    }

    return { ...config };
}
export async function getUserInfo(): Promise<UserInfo> {
    try {
        const response = await fetch("/.auth/me");
        console.log("Fetching user info from: ", "/.auth/me");
        console.log("Response ", response);
        if (!response.ok) {
            console.log(
                "No identity provider found. Access to chat will be blocked."
            );
            return {} as UserInfo;
        }
        const payload = await response.json();
        console.log("User info payload: ", payload[0]);
        const userInfo: UserInfo = {
            access_token: payload[0].access_token || "",
            expires_on: payload[0].expires_on || "",
            id_token: payload[0].id_token || "",
            provider_name: payload[0].provider_name || "",
            user_claims: payload[0].user_claims || [],
            user_email: payload[0].user_id || "",
            user_first_last_name: payload[0].user_claims?.find((claim: claim) => claim.typ === 'name')?.val || "",
            user_id: payload[0].user_claims?.find((claim: claim) => claim.typ === 'http://schemas.microsoft.com/identity/claims/objectidentifier')?.val || '',
        };
        console.log("User info: ", userInfo);
        return userInfo;
    } catch (e) {
        return {} as UserInfo;
    }
}
export function getApiUrl() {
    if (!API_URL) {
        // Check if window.appConfig exists
        if (window.appConfig && window.appConfig.API_URL) {
            setApiUrl(window.appConfig.API_URL);
        }
    }

    if (!API_URL) {
        console.info('API URL not yet configured');
        return null;
    }

    return API_URL;
}
export function getUserInfoGlobal() {
    if (!USER_INFO) {
        // Check if window.userInfo exists
        if (window.userInfo) {
            setUserInfoGlobal(window.userInfo);
        }
    }

    if (!USER_INFO) {
        console.info('User info not yet configured');
        return null;
    }

    return USER_INFO;
}

export function getUserId(): string {
    // USER_ID = getUserInfoGlobal()?.user_id || null;
    if (!USER_ID) {
        USER_ID = getUserInfoGlobal()?.user_id || null;
    }
    const userId = USER_ID ?? "00000000-0000-0000-0000-000000000000";
    return userId;
}

/**
 * Build headers with authentication information
 * @param headers Optional additional headers to merge
 * @returns Combined headers object with authentication
 */
export function headerBuilder(headers?: Record<string, string>): Record<string, string> {
    let userId = getUserId();
    let defaultHeaders = {
        "x-ms-client-principal-id": String(userId) || "",  // Custom header
    };
    return {
        ...defaultHeaders,
        ...(headers ? headers : {})
    };
}
export const toBoolean = (value: any): boolean => {
    if (typeof value !== 'string') {
        return false;
    }
    return value.trim().toLowerCase() === 'true';
};
export default {
    setApiUrl,
    getApiUrl,
    toBoolean,
    getUserId,
    getConfigData,
    setEnvData,
    config,
    USER_ID,
    API_URL
};
