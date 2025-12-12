import { useState } from 'react';
import { X } from 'lucide-react';
import { goalsAPI } from '../lib/api';

interface CalculateGoalModalProps {
  onClose: () => void;
  onCalculated: (goal: any) => void;
  date: string;
}

export default function CalculateGoalModal({
  onClose,
  onCalculated,
  date,
}: CalculateGoalModalProps) {
  const [formData, setFormData] = useState({
    age: '' as string | number,
    gender: 'male' as 'male' | 'female',
    weight: '' as string | number,
    height: '' as string | number,
    activity_level: 'moderate' as 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Валидация полей
    if (!formData.age || formData.age === '' || formData.age === 0) {
      setError('Пожалуйста, укажите возраст');
      return;
    }
    if (!formData.weight || formData.weight === '' || formData.weight === 0) {
      setError('Пожалуйста, укажите вес');
      return;
    }
    if (!formData.height || formData.height === '' || formData.height === 0) {
      setError('Пожалуйста, укажите рост');
      return;
    }
    
    setLoading(true);

    try {
      // Преобразуем значения в числа
      const age = typeof formData.age === 'string' && formData.age !== '' ? parseInt(formData.age) : (typeof formData.age === 'number' ? formData.age : 0);
      const weight = typeof formData.weight === 'string' && formData.weight !== '' ? parseFloat(formData.weight) : (typeof formData.weight === 'number' ? formData.weight : 0);
      const height = typeof formData.height === 'string' && formData.height !== '' ? parseInt(formData.height) : (typeof formData.height === 'number' ? formData.height : 0);
      
      const calculated = await goalsAPI.calculate(date, {
        age: age,
        gender: formData.gender,
        weight: weight,
        height: height,
        activity_level: formData.activity_level,
      });
      setResult(calculated);
    } catch (err: any) {
      const errorData = err.response?.data;
      if (errorData) {
        const errorMessages = Object.values(errorData).flat() as string[];
        setError(errorMessages.join(', '));
      } else {
        setError('Ошибка при расчёте целей');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!result) return;

    try {
      await goalsAPI.create(date, {
        calories: result.calories,
        proteins: result.proteins,
        fats: result.fats,
        carbohydrates: result.carbohydrates,
      });
      onCalculated(result);
    } catch (err: any) {
      setError('Ошибка при сохранении целей');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Автоматический расчёт</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          {!result ? (
            <form onSubmit={handleCalculate} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Возраст *
                </label>
                <input
                  type="number"
                  min="1"
                  max="120"
                  value={formData.age === '' ? '' : formData.age}
                  onChange={(e) => {
                    const val = e.target.value;
                    setFormData({ ...formData, age: val === '' ? '' : (parseInt(val) || '') });
                  }}
                  onFocus={(e) => e.target.select()}
                  placeholder="Введите возраст"
                  required
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Пол *
                </label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value as 'male' | 'female' })}
                  required
                  className="input-field"
                >
                  <option value="male">Мужской</option>
                  <option value="female">Женский</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Вес (кг) *
                </label>
                <input
                  type="number"
                  min="1"
                  max="300"
                  step="0.1"
                  value={formData.weight === '' ? '' : formData.weight}
                  onChange={(e) => {
                    const val = e.target.value;
                    setFormData({ ...formData, weight: val === '' ? '' : (parseFloat(val) || '') });
                  }}
                  onFocus={(e) => e.target.select()}
                  placeholder="Введите вес в кг"
                  required
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Рост (см) *
                </label>
                <input
                  type="number"
                  min="50"
                  max="250"
                  value={formData.height === '' ? '' : formData.height}
                  onChange={(e) => {
                    const val = e.target.value;
                    setFormData({ ...formData, height: val === '' ? '' : (parseInt(val) || '') });
                  }}
                  onFocus={(e) => e.target.select()}
                  placeholder="Введите рост в см"
                  required
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Уровень активности *
                </label>
                <select
                  value={formData.activity_level}
                  onChange={(e) => setFormData({ ...formData, activity_level: e.target.value as any })}
                  required
                  className="input-field"
                >
                  <option value="sedentary">Малоподвижный (сидячий образ жизни)</option>
                  <option value="light">Лёгкая активность (лёгкие упражнения 1-3 раза в неделю)</option>
                  <option value="moderate">Умеренная активность (умеренные упражнения 3-5 раз в неделю)</option>
                  <option value="active">Высокая активность (интенсивные упражнения 6-7 раз в неделю)</option>
                  <option value="very_active">Очень высокая активность (тяжёлые упражнения 6-7 раз в неделю)</option>
                </select>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 btn-secondary"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 btn-primary disabled:opacity-50"
                >
                  {loading ? 'Расчёт...' : 'Рассчитать'}
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-primary-50 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-3">Рассчитанные цели:</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Калории:</span>
                    <span className="font-semibold">{result.calories} ккал</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Белки:</span>
                    <span className="font-semibold">{result.proteins} г</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Жиры:</span>
                    <span className="font-semibold">{result.fats} г</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Углеводы:</span>
                    <span className="font-semibold">{result.carbohydrates} г</span>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setResult(null)}
                  className="flex-1 btn-secondary"
                >
                  Изменить
                </button>
                <button
                  onClick={handleApply}
                  className="flex-1 btn-primary"
                >
                  Применить
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

