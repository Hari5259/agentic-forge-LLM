# 📊 AgentForge Database Viewer
*Last updated: 2026-07-07 09:44:21*

## 🤖 Agents (`agents` table)
| Agent ID | Name | Type | Created At | Last Active | Active |
| --- | --- | --- | --- | --- | --- |
| `b6d7ad93` | **Resume Screener** | `hr_assistant` | 2026-07-07T09:19:09.701081 | 2026-07-07T09:34:49.740587 | ✅ Yes |
| `2e6dc700` | **Resume Sifter** | `hr_assistant` | 2026-07-07T09:19:34.534716 | 2026-07-07T09:19:34.534716 | ❌ No |
| `59e0fe2c` | **Resume Screen Helper** | `hr_assistant` | 2026-07-07T09:25:23.290804 | 2026-07-07T09:25:23.290804 | ✅ Yes |
| `fbfe221e` | **Email Composer** | `email_assistant` | 2026-07-07T09:29:24.887718 | 2026-07-07T09:29:24.887718 | ✅ Yes |
| `af1e43e5` | **Hackathon Invite Assistant** | `email_assistant` | 2026-07-07T09:31:38.557994 | 2026-07-07T09:38:44.873064 | ✅ Yes |
| `cd073d43` | **Professional Email Composer** | `email_assistant` | 2026-07-07T09:32:13.798552 | 2026-07-07T09:32:13.798552 | ✅ Yes |

## 💬 Conversations (`conversations` table)
| ID | Agent ID | Role | Content | Timestamp |
| --- | --- | --- | --- | --- |
| 6 | `af1e43e5` | **assistant** | I'd be happy to help you draft a professional business email inviting students to your company hackathon! Here's a suggested email:<br><br>Subject: Exciting Opportunity: Join Our Company Hackathon!<br><br>Dear [Student Name],<br><br>We're thrilled to announce that our company is hosting a hackathon,... | 2026-07-07T09:38:44.863479 |
| 5 | `af1e43e5` | **user** | to invite students for company hackathon | 2026-07-07T09:38:44.844619 |
| 4 | `b6d7ad93` | **assistant** | Based on the provided resumes (Source 1, Source 2, and Source 3), I can assess the candidates' skills and experience. Here's my evaluation:<br><br>**Resume Screening Report**<br><br>After analyzing the three resumes, I identified common themes and skills that stood out across all three documents. He... | 2026-07-07T09:34:49.731351 |
| 3 | `b6d7ad93` | **user** | generate a clean email for students | 2026-07-07T09:34:49.712205 |
| 2 | `b6d7ad93` | **assistant** | Based on the provided resumes (Source 1, Source 2, and Source 3), I can assess the candidate's skills and experience in relation to LLMs and Python.<br><br>From what I've analyzed, it appears that this candidate has significant experience working with Local LLMs, Retrieval-Augmented Generation (RAG)... | 2026-07-07T09:27:41.560343 |
| 1 | `b6d7ad93` | **user** | does he is well done with LLm and python | 2026-07-07T09:27:41.549803 |

## ⚙️ Action Logs (`action_logs` table)
| ID | Agent ID | Action Type | Result | Timestamp |
| --- | --- | --- | --- | --- |
| 3 | `af1e43e5` | `general_responder` | success | 2026-07-07T09:38:44.881885 |
| 2 | `b6d7ad93` | `general_responder` | success | 2026-07-07T09:34:49.749190 |
| 1 | `b6d7ad93` | `general_responder` | success | 2026-07-07T09:27:41.578718 |

## 📚 Knowledge Sources (`knowledge_sources` table)
| ID | Agent ID | Source Name | Source Type | Chunks |
| --- | --- | --- | --- | --- |
| 1 | `b6d7ad93` | **tmpb8thtpnu.pdf** | `pdf` | 4 |
| 2 | `b6d7ad93` | **tmp_4ph22qi.pdf** | `pdf` | 4 |
| 3 | `b6d7ad93` | **tmp3cf2koug.pdf** | `pdf` | 4 |
| 4 | `b6d7ad93` | **tmp9ojl91ar.pdf** | `pdf` | 4 |
| 5 | `b6d7ad93` | **tmp8o689qnc.pdf** | `pdf` | 4 |
| 6 | `b6d7ad93` | **tmpc2mkcpqw.pdf** | `pdf` | 4 |
| 7 | `b6d7ad93` | **tmppp51qhcc.pdf** | `pdf` | 4 |
