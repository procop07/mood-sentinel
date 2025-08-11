import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

def semantic_summary(analysis_results: List[Dict[str, Any]], 
                    time_period: str = "24h") -> Dict[str, Any]:
    """
    Создает семантическое резюме результатов анализа настроения.
    
    Args:
        analysis_results: Список результатов анализа с временными метками
        time_period: Временной период для анализа ('24h', '7d', '30d')
    
    Returns:
        Словарь с семантическим резюме, содержащим:
        - общую статистику
        - тренды настроения
        - ключевые паттерны
        - рекомендации
    """
    
    if not analysis_results:
        return {
            "summary": "Нет данных для анализа",
            "period": time_period,
            "total_entries": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    # Фильтрация данных по временному периоду
    filtered_results = _filter_by_time_period(analysis_results, time_period)
    
    if not filtered_results:
        return {
            "summary": f"Нет данных за период {time_period}",
            "period": time_period,
            "total_entries": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    # Базовая статистика
    stats = _calculate_basic_stats(filtered_results)
    
    # Анализ трендов
    trends = _analyze_trends(filtered_results, time_period)
    
    # Выявление паттернов
    patterns = _identify_patterns(filtered_results)
    
    # Генерация рекомендаций
    recommendations = _generate_recommendations(stats, trends, patterns)
    
    # Создание семантического резюме
    summary_text = _create_semantic_text(stats, trends, patterns)
    
    return {
        "summary": summary_text,
        "period": time_period,
        "total_entries": len(filtered_results),
        "statistics": stats,
        "trends": trends,
        "patterns": patterns,
        "recommendations": recommendations,
        "timestamp": datetime.now().isoformat()
    }

def _filter_by_time_period(results: List[Dict], period: str) -> List[Dict]:
    """Фильтрует результаты по временному периоду."""
    now = datetime.now()
    
    if period == "24h":
        cutoff = now - timedelta(hours=24)
    elif period == "7d":
        cutoff = now - timedelta(days=7)
    elif period == "30d":
        cutoff = now - timedelta(days=30)
    else:
        return results
    
    filtered = []
    for result in results:
        if 'timestamp' in result:
            try:
                result_time = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                if result_time >= cutoff:
                    filtered.append(result)
            except (ValueError, TypeError):
                # Если нет валидной временной метки, включаем запись
                filtered.append(result)
        else:
            filtered.append(result)
    
    return filtered

def _calculate_basic_stats(results: List[Dict]) -> Dict[str, Any]:
    """Вычисляет базовую статистику по результатам."""
    risk_levels = Counter()
    flag_counts = defaultdict(int)
    total_flags = 0
    
    for result in results:
        if 'overall_risk_level' in result:
            risk_levels[result['overall_risk_level']] += 1
        
        # Подсчет различных типов флагов
        for flag_type in ['depression', 'anxiety', 'anger', 'substance_abuse']:
            if flag_type in result and result[flag_type].get('detected', False):
                flag_counts[flag_type] += result[flag_type].get('count', 1)
                total_flags += 1
    
    return {
        "risk_distribution": dict(risk_levels),
        "flag_counts": dict(flag_counts),
        "total_flags_detected": total_flags,
        "entries_with_flags": sum(1 for r in results if any(
            r.get(flag, {}).get('detected', False) 
            for flag in ['depression', 'anxiety', 'anger', 'substance_abuse']
        )),
        "flag_rate": total_flags / len(results) if results else 0
    }

def _analyze_trends(results: List[Dict], period: str) -> Dict[str, Any]:
    """Анализирует тренды в данных."""
    if len(results) < 2:
        return {"trend": "insufficient_data", "direction": "unknown"}
    
    # Сортировка по времени
    time_sorted = sorted(
        [r for r in results if 'timestamp' in r],
        key=lambda x: x.get('timestamp', '')
    )
    
    if len(time_sorted) < 2:
        return {"trend": "no_time_data", "direction": "unknown"}
    
    # Разделяем на первую и вторую половину периода
    mid_point = len(time_sorted) // 2
    first_half = time_sorted[:mid_point]
    second_half = time_sorted[mid_point:]
    
    # Подсчет критических случаев в каждой половине
    first_critical = sum(1 for r in first_half 
                        if r.get('overall_risk_level') in ['high', 'critical'])
    second_critical = sum(1 for r in second_half 
                         if r.get('overall_risk_level') in ['high', 'critical'])
    
    # Определяем тренд
    if second_critical > first_critical:
        trend = "worsening"
        direction = "up"
    elif second_critical < first_critical:
        trend = "improving"
        direction = "down"
    else:
        trend = "stable"
        direction = "stable"
    
    return {
        "trend": trend,
        "direction": direction,
        "first_half_critical": first_critical,
        "second_half_critical": second_critical,
        "change_magnitude": abs(second_critical - first_critical)
    }

def _identify_patterns(results: List[Dict]) -> Dict[str, Any]:
    """Выявляет повторяющиеся паттерны в данных."""
    patterns = {
        "most_common_flags": [],
        "flag_combinations": [],
        "peak_risk_times": [],
        "dominant_emotions": []
    }
    
    # Наиболее частые флаги
    flag_frequency = defaultdict(int)
    flag_combinations = defaultdict(int)
    
    for result in results:
        active_flags = []
        for flag_type in ['depression', 'anxiety', 'anger', 'substance_abuse']:
            if flag_type in result and result[flag_type].get('detected', False):
                flag_frequency[flag_type] += 1
                active_flags.append(flag_type)
        
        # Комбинации флагов
        if len(active_flags) > 1:
            combo = tuple(sorted(active_flags))
            flag_combinations[combo] += 1
    
    # Топ-3 наиболее частых флагов
    patterns["most_common_flags"] = [
        {"flag": flag, "count": count} 
        for flag, count in Counter(flag_frequency).most_common(3)
    ]
    
    # Топ-3 комбинации флагов
    patterns["flag_combinations"] = [
        {"combination": list(combo), "count": count}
        for combo, count in Counter(flag_combinations).most_common(3)
    ]
    
    return patterns

def _generate_recommendations(stats: Dict, trends: Dict, patterns: Dict) -> List[str]:
    """Генерирует рекомендации на основе анализа."""
    recommendations = []
    
    # Рекомендации на основе статистики
    if stats.get('flag_rate', 0) > 0.5:
        recommendations.append(
            "Высокий уровень выявленных тревожных сигналов. "
            "Рекомендуется усилить мониторинг и профилактические меры."
        )
    
    # Рекомендации на основе трендов
    if trends.get('trend') == 'worsening':
        recommendations.append(
            "Наблюдается ухудшение показателей. "
            "Необходимо срочное вмешательство специалистов."
        )
    elif trends.get('trend') == 'improving':
        recommendations.append(
            "Положительная динамика. Продолжайте текущие меры поддержки."
        )
    
    # Рекомендации на основе паттернов
    if patterns.get('most_common_flags'):
        top_flag = patterns['most_common_flags'][0]['flag']
        if top_flag == 'depression':
            recommendations.append(
                "Преобладают признаки депрессии. "
                "Рекомендуется консультация с психологом или психиатром."
            )
        elif top_flag == 'anxiety':
            recommendations.append(
                "Высокий уровень тревожности. "
                "Полезны техники релаксации и управления стрессом."
            )
    
    if not recommendations:
        recommendations.append(
            "Показатели в пределах нормы. Продолжайте регулярный мониторинг."
        )
    
    return recommendations

def _create_semantic_text(stats: Dict, trends: Dict, patterns: Dict) -> str:
    """Создает семантическое текстовое резюме."""
    
    # Базовое резюме
    total_entries = stats.get('entries_with_flags', 0)
    if total_entries == 0:
        return "За анализируемый период тревожных сигналов не обнаружено."
    
    summary_parts = []
    
    # Информация о количестве сигналов
    if total_entries == 1:
        summary_parts.append("Обнаружен 1 тревожный сигнал")
    else:
        summary_parts.append(f"Обнаружено {total_entries} тревожных сигналов")
    
    # Информация о тренде
    trend_info = trends.get('trend', 'unknown')
    if trend_info == 'worsening':
        summary_parts.append("с тенденцией к ухудшению")
    elif trend_info == 'improving':
        summary_parts.append("с положительной динамикой")
    elif trend_info == 'stable':
        summary_parts.append("с стабильными показателями")
    
    # Информация о доминирующих паттернах
    if patterns.get('most_common_flags'):
        top_flag = patterns['most_common_flags'][0]['flag']
        flag_names = {
            'depression': 'депрессивных состояний',
            'anxiety': 'тревожности', 
            'anger': 'агрессивности',
            'substance_abuse': 'злоупотребления веществами'
        }
        if top_flag in flag_names:
            summary_parts.append(f"Преобладают признаки {flag_names[top_flag]}")
    
    # Объединяем части резюме
    summary = ". ".join(summary_parts) + "."
    
    # Добавляем общую оценку риска
    risk_dist = stats.get('risk_distribution', {})
    critical_count = risk_dist.get('critical', 0) + risk_dist.get('high', 0)
    
    if critical_count > 0:
        summary += f" Выявлено {critical_count} случаев высокого риска, требующих немедленного внимания."
    
    return summary
