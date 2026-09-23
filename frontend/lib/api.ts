export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data as { detail?: string }).detail || `خطأ ${res.status}`);
  }
  return data as T;
}

export interface Subject {
  id: number;
  name: string;
  description: string | null;
  icon: string | null;
  image_url: string | null;
  is_active: boolean;
  display_order: number;
  lessons_count: number;
}

export interface Lesson {
  id: number;
  subject_id: number;
  subject_name: string | null;
  title: string;
  description: string | null;
  content: string | null;
  display_order: number;
  is_published: boolean;
  scheduled_at: string | null;
}

export interface Progress {
  id: number;
  lesson_id: number;
  subject_id: number | null;
  is_completed: boolean;
  last_score: number | null;
  completed_at: string | null;
  last_accessed_at: string;
}

export interface SubjectProgress {
  subject_id: number;
  total_lessons: number;
  completed_lessons: number;
  progress_percentage: number;
}

export interface Quiz {
  id: number;
  lesson_id: number;
  lesson_title: string | null;
  title: string;
  description: string | null;
  is_active: boolean;
  questions_count: number;
}

export interface QuizQuestion {
  id: number;
  quiz_id: number;
  question_text: string;
  question_type: string;
  options: string[] | null;
  points: number;
  display_order: number;
}

export interface QuizQuestionAdmin extends QuizQuestion {
  correct_answer: string;
  explanation: string | null;
}

export interface QuizDetail extends Quiz {
  questions: QuizQuestion[];
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  score: number;
  total_points: number;
  percentage: number;
  started_at: string;
  completed_at: string | null;
  answers_count: number;
}

export interface QuizAnswerResult {
  question_id: number;
  question_text: string;
  question_type: string;
  your_answer: string | null;
  correct_answer: string;
  is_correct: boolean;
  points_earned: number;
  points: number;
  explanation: string | null;
}

export interface QuizResult {
  attempt_id: number;
  quiz_id: number;
  quiz_title: string;
  score: number;
  total_points: number;
  percentage: number;
  correct_count: number;
  wrong_count: number;
  completed_at: string | null;
  answers: QuizAnswerResult[];
}

export interface AiSource {
  document_id: number;
  chunk_id: number;
  title: string;
}

export interface AiAskResponse {
  answer: string;
  sources: AiSource[];
  grounded: boolean;
}

export interface LessonDocument {
  id: number;
  lesson_id: number;
  lesson_title: string | null;
  title: string;
  source_type: string;
  source_path: string | null;
  status: string;
  chunks_count: number;
}

export interface Weakness {
  id: number;
  lesson_id: number;
  lesson_title: string | null;
  topic: string;
  attempt_count: number;
  correct_count: number;
  mistake_count: number;
  mastery_score: number | null;
  confidence: number;
  sample_size: number;
  severity: string;
  last_mistake_at: string | null;
  last_reviewed_at: string | null;
}

export interface Mistake {
  id: number;
  lesson_id: number;
  lesson_title: string | null;
  question_id: number | null;
  question_text: string | null;
  mistake_key: string;
  mistake_count: number;
  is_recurring: boolean;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
}

export interface LearningProfile {
  overall_mastery: number | null;
  lessons_completed: number;
  quizzes_completed: number;
  weak_lessons: { lesson_id: number; lesson_title: string; subject_id: number | null; mastery_score: number; severity: string; confidence: number; sample_size: number }[];
  recurring_mistakes: { lesson_id: number; lesson_title: string; question_id: number | null; question_text: string | null; mistake_count: number; last_seen_at: string }[];
  recent_performance: { quiz_id: number; quiz_title: string; percentage: number; completed_at: string | null }[];
}

export interface ReviewItem {
  lesson_id: number;
  lesson_title: string;
  subject_id: number | null;
  quiz_id: number | null;
  kind: string;
  reason: string;
  priority: number;
  mastery: number;
  due_at?: string | null;
  review_count?: number;
  last_reviewed_at?: string | null;
}

export interface ReviewPlan {
  date: string;
  items: ReviewItem[];
}

export interface ReviewSchedule {
  id: number;
  lesson_id: number;
  lesson_title: string | null;
  subject_id: number | null;
  quiz_id: number | null;
  due_at: string | null;
  last_reviewed_at: string | null;
  review_count: number;
  interval_days: number;
  priority: number;
  status: string;
}

export interface ReviewScheduleList {
  today: ReviewSchedule[];
  upcoming: ReviewSchedule[];
}
