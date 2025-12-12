import { useState, useRef } from 'react';
import { X, Upload, Camera } from 'lucide-react';
import { dishesAPI } from '../lib/api';

interface RecognizeDishModalProps {
  date: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function RecognizeDishModal({
  date,
  onClose,
  onSuccess,
}: RecognizeDishModalProps) {
  const [image, setImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recognized, setRecognized] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setError('Размер файла не должен превышать 10 МБ');
        return;
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target?.result as string);
        setError('');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRecognize = async () => {
    if (!image) return;

    setLoading(true);
    setError('');

    try {
      // Передаём полный base64 с префиксом (API сам обработает)
      const result = await dishesAPI.recognize({
        image_base64: image,
        date,
      });

      setRecognized(result);
    } catch (err: any) {
      const errorData = err.response?.data;
      if (errorData?.detail) {
        setError(errorData.detail);
      } else {
        setError('Ошибка при распознавании блюда');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDish = async (dishData: any, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => {
    try {
      await dishesAPI.create({
        name: dishData.name,
        date,
        meal_type: mealType,
        weight: dishData.weight,
        calories: dishData.calories,
        proteins: dishData.proteins,
        fats: dishData.fats,
        carbohydrates: dishData.carbohydrates,
      });
      onSuccess();
    } catch (err: any) {
      setError('Ошибка при создании блюда');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Распознать блюдо</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {!recognized ? (
            <>
              {!image ? (
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary-400 transition-colors">
                    <Upload className="mx-auto mb-4 text-gray-400" size={48} />
                    <p className="text-gray-600 mb-4">Загрузите фотографию блюда</p>
                    <div className="flex items-center justify-center space-x-4">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="btn-primary"
                      >
                        Выбрать файл
                      </button>
                      <button
                        type="button"
                        onClick={() => cameraInputRef.current?.click()}
                        className="btn-secondary flex items-center space-x-2"
                      >
                        <Camera size={20} />
                        <span>Сфотографировать</span>
                      </button>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <input
                      ref={cameraInputRef}
                      type="file"
                      accept="image/*"
                      capture="environment"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="relative">
                    <img
                      src={image}
                      alt="Preview"
                      className="w-full h-64 object-cover rounded-lg"
                    />
                    <button
                      onClick={() => setImage(null)}
                      className="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-lg hover:bg-opacity-70"
                    >
                      <X size={20} />
                    </button>
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setImage(null)}
                      className="flex-1 btn-secondary"
                    >
                      Выбрать другое
                    </button>
                    <button
                      onClick={handleRecognize}
                      disabled={loading}
                      className="flex-1 btn-primary disabled:opacity-50"
                    >
                      {loading ? 'Распознавание...' : 'Распознать'}
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-3">Блюдо распознано!</h3>
                {recognized.recognized_dishes?.map((dish: any, index: number) => (
                  <div key={index} className="mb-4 last:mb-0">
                    <div className="font-medium text-gray-900 mb-2">{dish.name}</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>Вес: {dish.weight} г</div>
                      <div>Калории: {dish.calories} ккал</div>
                      <div>Белки: {dish.proteins} г</div>
                      <div>Жиры: {dish.fats} г</div>
                      <div>Углеводы: {dish.carbohydrates} г</div>
                      {dish.confidence && (
                        <div>Уверенность: {Math.round(dish.confidence * 100)}%</div>
                      )}
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleCreateDish(dish, 'breakfast')}
                        className="px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
                      >
                        Завтрак
                      </button>
                      <button
                        onClick={() => handleCreateDish(dish, 'lunch')}
                        className="px-3 py-2 text-sm bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200"
                      >
                        Обед
                      </button>
                      <button
                        onClick={() => handleCreateDish(dish, 'dinner')}
                        className="px-3 py-2 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200"
                      >
                        Ужин
                      </button>
                      <button
                        onClick={() => handleCreateDish(dish, 'snack')}
                        className="px-3 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                      >
                        Перекус
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setRecognized(null);
                    setImage(null);
                  }}
                  className="flex-1 btn-secondary"
                >
                  Распознать другое
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 btn-primary"
                >
                  Готово
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

