import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { EquipmentPage } from '@/modules/equipment/EquipmentPage';
import { DocumentsPage } from '@/modules/documents/DocumentsPage';
import { TechCardsPage } from '@/modules/tech-cards/TechCardsPage';
import { InstructionsPage } from '@/modules/instructions/InstructionsPage';
import { CoursesPage } from '@/modules/courses/CoursesPage';
import { CompetenciesPage } from '@/modules/competencies/CompetenciesPage';
import { AdminPage } from '@/modules/admin/AdminPage';
import { KnowledgeSearchPage } from '@/modules/knowledge/KnowledgeSearchPage';
import { LoginPage } from '@/modules/auth/LoginPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/equipment" replace />} />
        <Route path="equipment" element={<EquipmentPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="tech-cards" element={<TechCardsPage />} />
        <Route path="instructions" element={<InstructionsPage />} />
        <Route path="courses" element={<CoursesPage />} />
        <Route path="competencies" element={<CompetenciesPage />} />
        <Route path="knowledge" element={<KnowledgeSearchPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>
    </Routes>
  );
}
