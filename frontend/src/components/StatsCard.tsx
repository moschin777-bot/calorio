interface StatsCardProps {
  summary: {
    total_calories: number;
    total_proteins: number;
    total_fats: number;
    total_carbohydrates: number;
    goal_progress?: {
      calories_percent: number;
      proteins_percent: number;
      fats_percent: number;
      carbohydrates_percent: number;
    };
  };
  goal: {
    calories: number;
    proteins: number;
    fats: number;
    carbohydrates: number;
  } | null;
}

export default function StatsCard({ summary, goal }: StatsCardProps) {
  const getProgressColor = (percent: number) => {
    if (percent >= 100) return 'text-green-600';
    if (percent >= 75) return 'text-blue-600';
    if (percent >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProgressBarColor = (percent: number) => {
    if (percent >= 100) return 'bg-green-500';
    if (percent >= 75) return 'bg-blue-500';
    if (percent >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Статистика за день</h3>

      <div className="space-y-4">
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-600">Калории:</span>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-gray-900">
                {summary.total_calories || 0} ккал
              </span>
              {goal && summary.goal_progress && (
                <span className={`text-sm font-medium ${getProgressColor(summary.goal_progress.calories_percent)}`}>
                  {Math.round(summary.goal_progress.calories_percent)}%
                </span>
              )}
            </div>
          </div>
          {goal && summary.goal_progress && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getProgressBarColor(summary.goal_progress.calories_percent)}`}
                style={{ width: `${Math.min(summary.goal_progress.calories_percent, 100)}%` }}
              />
            </div>
          )}
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-600">Белки:</span>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-blue-600">
                {summary.total_proteins || 0} г
              </span>
              {goal && summary.goal_progress && (
                <span className={`text-sm font-medium ${getProgressColor(summary.goal_progress.proteins_percent)}`}>
                  {Math.round(summary.goal_progress.proteins_percent)}%
                </span>
              )}
            </div>
          </div>
          {goal && summary.goal_progress && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getProgressBarColor(summary.goal_progress.proteins_percent)}`}
                style={{ width: `${Math.min(summary.goal_progress.proteins_percent, 100)}%` }}
              />
            </div>
          )}
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-600">Жиры:</span>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-yellow-600">
                {summary.total_fats || 0} г
              </span>
              {goal && summary.goal_progress && (
                <span className={`text-sm font-medium ${getProgressColor(summary.goal_progress.fats_percent)}`}>
                  {Math.round(summary.goal_progress.fats_percent)}%
                </span>
              )}
            </div>
          </div>
          {goal && summary.goal_progress && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getProgressBarColor(summary.goal_progress.fats_percent)}`}
                style={{ width: `${Math.min(summary.goal_progress.fats_percent, 100)}%` }}
              />
            </div>
          )}
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-600">Углеводы:</span>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-green-600">
                {summary.total_carbohydrates || 0} г
              </span>
              {goal && summary.goal_progress && (
                <span className={`text-sm font-medium ${getProgressColor(summary.goal_progress.carbohydrates_percent)}`}>
                  {Math.round(summary.goal_progress.carbohydrates_percent)}%
                </span>
              )}
            </div>
          </div>
          {goal && summary.goal_progress && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getProgressBarColor(summary.goal_progress.carbohydrates_percent)}`}
                style={{ width: `${Math.min(summary.goal_progress.carbohydrates_percent, 100)}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

