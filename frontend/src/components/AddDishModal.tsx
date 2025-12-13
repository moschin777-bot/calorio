import { useState, useEffect } from 'react';
import { X, Search } from 'lucide-react';
import { dishesAPI } from '../lib/api';

interface AddDishModalProps {
  date: string;
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddDishModal({
  date,
  mealType,
  onClose,
  onSuccess,
}: AddDishModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    weight: 100,
    calories: 0,
    proteins: 0,
    fats: 0,
    carbohydrates: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchingNutrition, setSearchingNutrition] = useState(false);
  const [nutritionError, setNutritionError] = useState('');

  const handleSearchNutrition = async () => {
    if (!formData.name.trim()) {
      setNutritionError('Введите название блюда');
      return;
    }
    
    setSearchingNutrition(true);
    setNutritionError('');
    
    try {
      const nutrition = await dishesAPI.searchNutrition(formData.name, formData.weight);
      setFormData({
        ...formData,
        calories: nutrition.calories || 0,
        proteins: nutrition.proteins || 0,
        fats: nutrition.fats || 0,
        carbohydrates: nutrition.carbohydrates || 0,
      });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Не удалось найти информацию о продукте';
      setNutritionError(errorMsg);
    } finally {
      setSearchingNutrition(false);
    }
  };

  // Автоматический поиск КБЖУ при изменении названия (с задержкой)
  useEffect(() => {
    if (!formData.name.trim() || formData.name.length < 3) {
      return;
    }
    
    // Проверяем, что КБЖУ еще не заполнены
    if (formData.calories !== 0 || formData.proteins !== 0 || formData.fats !== 0 || formData.carbohydrates !== 0) {
      return;
    }
    
    const timeoutId = setTimeout(async () => {
      setSearchingNutrition(true);
      setNutritionError('');
      
      try {
        const nutrition = await dishesAPI.searchNutrition(formData.name, formData.weight);
        setFormData(prev => ({
          ...prev,
          calories: nutrition.calories || 0,
          proteins: nutrition.proteins || 0,
          fats: nutrition.fats || 0,
          carbohydrates: nutrition.carbohydrates || 0,
        }));
      } catch (err: any) {
        // Не показываем ошибку при автоматическом поиске, только при ручном
        setNutritionError('');
      } finally {
        setSearchingNutrition(false);
      }
    }, 1500); // Задержка 1.5 секунды после окончания ввода
    
    return () => clearTimeout(timeoutId);
  }, [formData.name, formData.weight]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Отправляем только заполненные поля КБЖУ (если они не равны 0)
      const payload: any = {
        name: formData.name,
        date,
        meal_type: mealType,
        weight: formData.weight,
      };
      
      // Добавляем КБЖУ только если они заполнены (не равны 0)
      if (formData.calories > 0) payload.calories = formData.calories;
      if (formData.proteins > 0) payload.proteins = formData.proteins;
      if (formData.fats > 0) payload.fats = formData.fats;
      if (formData.carbohydrates > 0) payload.carbohydrates = formData.carbohydrates;
      
      await dishesAPI.create(payload);
      onSuccess();
    } catch (err: any) {
      const errorData = err.response?.data;
      if (errorData) {
        const errorMessages = Object.values(errorData).flat() as string[];
        setError(errorMessages.join(', '));
      } else {
        setError('Ошибка при создании блюда');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Добавить блюдо</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Название блюда *
            </label>
            <div className="flex gap-2">
            <input
              type="text"
              value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value });
                  setNutritionError('');
                }}
              required
                className="input-field flex-1"
              placeholder="Например, Овсянка с фруктами"
            />
              <button
                type="button"
                onClick={handleSearchNutrition}
                disabled={searchingNutrition || !formData.name.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                title="Найти КБЖУ по названию"
              >
                <Search size={18} />
                {searchingNutrition ? 'Поиск...' : 'Найти'}
              </button>
            </div>
            {nutritionError && (
              <p className="mt-1 text-sm text-orange-600">{nutritionError}</p>
            )}
            {searchingNutrition && (
              <p className="mt-1 text-sm text-gray-500">Ищем информацию о продукте...</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Вес (г) *
            </label>
            <input
              type="number"
              min="1"
              value={formData.weight}
              onChange={(e) => setFormData({ ...formData, weight: parseInt(e.target.value) || 0 })}
              required
              className="input-field"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Калории (ккал)
              </label>
              <input
                type="number"
                min="0"
                value={formData.calories}
                onChange={(e) => setFormData({ ...formData, calories: parseInt(e.target.value) || 0 })}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Белки (г)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.proteins}
                onChange={(e) => {
                  const val = e.target.value.replace(',', '.');
                  setFormData({ ...formData, proteins: parseFloat(val) || 0 });
                }}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Жиры (г)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.fats}
                onChange={(e) => {
                  const val = e.target.value.replace(',', '.');
                  setFormData({ ...formData, fats: parseFloat(val) || 0 });
                }}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Углеводы (г)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.carbohydrates}
                onChange={(e) => {
                  const val = e.target.value.replace(',', '.');
                  setFormData({ ...formData, carbohydrates: parseFloat(val) || 0 });
                }}
                className="input-field"
              />
            </div>
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
              {loading ? 'Создание...' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

