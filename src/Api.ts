import axios from './api/index'

export interface CaseSummary {
    case_id: string
    company: string
    email_excerpt: string
    attachments: number
}

export interface CaseDetail {
    case_id: string
    company: string
    email_body: string
    llm_output: string
    attachments: Array<{
        type: string
        label: string
        filename: string
        download_url: string
    }>
}

export const API = {
    listCases: () => axios.get<{ cases: CaseSummary[] }>('/api/cases'),
    getCase: (caseId: string) => axios.get<CaseDetail>(`/api/cases/${caseId}`),
}