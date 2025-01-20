import {Amplify} from 'aws-amplify';
import {getCurrentUser, fetchAuthSession, signInWithRedirect} from 'aws-amplify/auth'
import { AwsClient } from 'aws4fetch';

export const basePath = 'threat-mitigation'
export const AwsConfig = {
    region: import.meta.env.VITE_APP_AWS_REGION,
    userPoolId: import.meta.env.VITE_APP_USER_POOL_ID,
    identityPoolId: import.meta.env.VITE_APP_IDENTITY_POOL_ID,
    userPoolClientId: import.meta.env.VITE_APP_USER_POOL_CLIENT_ID,
    userPoolDomain: import.meta.env.VITE_APP_COGNITO_DOMAIN,
    redirectSignIn: import.meta.env.VITE_APP_REDIRECT_SIGN_IN_URL,
    redirectSignOut: import.meta.env.VITE_APP_REDIRECT_SIGN_OUT_URL,
    endpoints: {
        diagramToText: import.meta.env.VITE_APP_ENDPOINT_DIAGRAM_TO_TEXT,
        summaryToThreatModel: import.meta.env.VITE_APP_ENDPOINT_SUMMARY_TO_THREAT_MODEL,
    }
}

Amplify.configure({
    Auth: {
        Cognito: {
            userPoolId: AwsConfig.userPoolId,
            identityPoolId: AwsConfig.identityPoolId,
            allowGuestAccess: false,
            userPoolClientId: AwsConfig.userPoolClientId,
            loginWith: {
                oauth: {
                    domain: AwsConfig.userPoolDomain,
                    scopes: [
                        "email",
                        "openid",
                        "profile"
                    ],
                    redirectSignIn: [AwsConfig.redirectSignIn],
                    redirectSignOut: [AwsConfig.redirectSignOut],
                    responseType: 'code',
                }
            }
        },
    },
});

export const getUser = async () => {
    try {
        return await getCurrentUser()
    } catch (error) {
        await signInWithRedirect()
        return null
    }
}

export const createFetcher = async (): Promise<typeof fetch> => {
    await getUser()
    const session = await fetchAuthSession()
    if (!session?.credentials) throw new Error('No credentials found')

    const client =  new AwsClient({
        accessKeyId: session.credentials.accessKeyId,
        secretAccessKey: session.credentials.secretAccessKey,
        sessionToken: session.credentials.sessionToken,
        region: AwsConfig.region,
        service: 'lambda',
    })
    return client.fetch.bind(client)
}


