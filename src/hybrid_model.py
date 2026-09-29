"""
信息显著性驱动的传染病混合仿真模型
核心模块：ABM + SD + DES 三层耦合

作者：AI Research Assistant
日期：2026-09-28
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import heapq


@dataclass
class Agent:
    """ABM层：个体Agent"""
    id: int
    state: str  # 'S', 'E', 'I', 'R'
    risk_perception: float = 0.0
    protection_level: float = 0.0
    info_saliency: float = 0.0
    infected_day: int = 0
    exposed_day: int = 0
    detected: bool = False
    hospital_admitted: bool = False
    in_queue: bool = False
    queue_start_time: int = 0


@dataclass
class SEIRParams:
    """SD层：SEIR模型参数"""
    beta_base: float = 0.3  # 基础传播率
    sigma: float = 0.2  # 潜伏期倒数（1/5天）
    gamma: float = 0.1  # 恢复率倒数（1/10天）
    hospitalization_rate: float = 0.15  # 住院率
    detection_rate: float = 0.3  # 检测率
    protection_efficiency: float = 0.85  # 防护效率（即使100%防护，仍有15%残余传播风险）


@dataclass
class DESParams:
    """DES层：医疗资源参数"""
    hospital_beds: int = 200
    icu_beds: int = 50
    testing_capacity: int = 100  # 每日检测能力
    avg_hospital_stay: int = 7  # 平均住院天数
    avg_icu_stay: int = 14  # 平均ICU天数
    test_result_time: int = 1  # 检测结果时间（天）


@dataclass
class MosquitoParams:
    """蚊媒动态参数（登革热通过蚊子传播）"""
    mosquito_population: int = 5000  # 蚊子种群数量
    biting_rate: float = 0.3  # 每日叮咬率
    transmission_human_to_mosquito: float = 0.5  # 人传蚊概率
    transmission_mosquito_to_human: float = 0.4  # 蚊传人概率
    mosquito_lifespan: int = 14  # 蚊子平均寿命（天）
    extrinsic_incubation_period: int = 10  # 外潜伏期（蚊子体内病毒发育时间）
    seasonal_factor: float = 1.0  # 季节性因子（可根据月份调整）


class MosquitoDynamicModel:
    """蚊媒动态模型（登革热特有）"""
    
    def __init__(self, params: MosquitoParams):
        self.params = params
        self.infected_mosquitoes = 0  # 感染蚊子数量
        self.exposed_mosquitoes = 0  # 潜伏期蚊子数量
        self.mosquito_history: List[Dict] = []
    
    def update(self, infected_humans: int, day: int) -> float:
        """
        更新蚊媒动态
        
        Args:
            infected_humans: 当前感染人数
            day: 当前天数
        
        Returns:
            蚊媒传播风险因子 [0, 1]
        """
        # 蚊子叮咬感染人类后，病毒在蚊子体内发育（外潜伏期）
        new_exposed = (
            self.params.biting_rate * 
            self.params.transmission_human_to_mosquito * 
            infected_humans * 
            (self.params.mosquito_population - self.infected_mosquitoes - self.exposed_mosquitoes) / 
            self.params.mosquito_population
        )
        
        # 外潜伏期结束后，蚊子变为感染状态
        new_infected = self.exposed_mosquitoes / self.params.extrinsic_incubation_period
        
        # 蚊子死亡
        mosquito_death = self.infected_mosquitoes / self.params.mosquito_lifespan
        
        # 更新状态
        self.exposed_mosquitoes = max(0, self.exposed_mosquitoes + new_exposed - new_infected)
        self.infected_mosquitoes = max(0, self.infected_mosquitoes + new_infected - mosquito_death)
        
        # 计算蚊媒传播风险因子
        mosquito_risk = (
            self.params.biting_rate * 
            self.params.transmission_mosquito_to_human * 
            self.infected_mosquitoes / 
            self.params.mosquito_population *
            self.params.seasonal_factor
        )
        
        # 记录历史
        self.mosquito_history.append({
            'day': day,
            'infected_mosquitoes': self.infected_mosquitoes,
            'exposed_mosquitoes': self.exposed_mosquitoes,
            'mosquito_risk': mosquito_risk
        })
        
        return min(1.0, mosquito_risk)


class InformationSaliencyModel:
    """信息显著性模型"""
    
    def __init__(self, media_amplification: float = 1.0, decay_rate: float = 0.1):
        self.media_amplification = media_amplification
        self.decay_rate = decay_rate
        self.info_history: List[float] = []
    
    def update(self, infected_count: int, total_population: int, day: int) -> float:
        """
        更新信息显著性
        
        Args:
            infected_count: 当前感染人数
            total_population: 总人口
            day: 当前天数
        
        Returns:
            信息显著性值 [0, 1]
        """
        # 基础显著性：感染比例
        base_saliency = infected_count / total_population
        
        # 媒体放大效应
        media_effect = base_saliency * self.media_amplification
        
        # 时间衰减（避免信息疲劳）
        temporal_decay = np.exp(-self.decay_rate * day / 100)
        
        # 综合显著性
        saliency = min(1.0, media_effect * temporal_decay)
        
        self.info_history.append(saliency)
        return saliency


class RiskPerceptionModel:
    """风险感知模型"""
    
    def __init__(self, info_weight: float = 0.6, social_weight: float = 0.3, 
                 personal_weight: float = 0.1, inertia: float = 0.3):
        self.info_weight = info_weight
        self.social_weight = social_weight
        self.personal_weight = personal_weight
        self.inertia = inertia  # 行为惯性
    
    def update_agent(self, agent: Agent, info_saliency: float, 
                    social_influence: float, personal_experience: float) -> float:
        """
        更新个体风险感知
        
        Args:
            agent: 个体Agent
            info_saliency: 信息显著性
            social_influence: 社会影响（周围人感染比例）
            personal_experience: 个人经历（是否感染或接触感染者）
        
        Returns:
            风险感知值 [0, 1]
        """
        # 加权综合
        target_risk = (
            self.info_weight * info_saliency +
            self.social_weight * social_influence +
            self.personal_weight * personal_experience
        )
        
        # 行为惯性（平滑更新）
        new_risk = (1 - self.inertia) * target_risk + self.inertia * agent.risk_perception
        
        agent.risk_perception = min(1.0, max(0.0, new_risk))
        return agent.risk_perception


class BehaviorModel:
    """行为决策模型"""
    
    def __init__(self, sensitivity: float = 1.5):
        self.sensitivity = sensitivity  # 风险感知敏感度
    
    def update_protection(self, agent: Agent) -> float:
        """
        更新防护行为
        
        Args:
            agent: 个体Agent
        
        Returns:
            防护水平 [0, 1]
        """
        # S型响应函数
        protection = 1.0 / (1.0 + np.exp(-self.sensitivity * (agent.risk_perception - 0.5)))
        agent.protection_level = protection
        return protection


class HospitalDES:
    """DES层：医院资源离散事件仿真"""
    
    def __init__(self, params: DESParams):
        self.params = params
        self.occupied_beds = 0
        self.occupied_icu = 0
        self.queue = []  # 等待住院的队列
        self.test_queue = []  # 检测队列
        self.discharge_events = []  # 出院事件
        self.rejected_count = 0
    
    def request_admission(self, agent: Agent, day: int, severe: bool = False) -> bool:
        """
        请求住院
        
        Args:
            agent: 个体Agent
            day: 当前天数
            severe: 是否重症（需要ICU）
        
        Returns:
            是否成功入院
        """
        if severe:
            if self.occupied_icu < self.params.icu_beds:
                self.occupied_icu += 1
                agent.hospital_admitted = True
                # 安排出院事件
                discharge_day = day + self.params.avg_icu_stay
                heapq.heappush(self.discharge_events, (discharge_day, agent.id, 'icu'))
                return True
            else:
                self.rejected_count += 1
                return False
        else:
            if self.occupied_beds < self.params.hospital_beds:
                self.occupied_beds += 1
                agent.hospital_admitted = True
                # 安排出院事件
                discharge_day = day + self.params.avg_hospital_stay
                heapq.heappush(self.discharge_events, (discharge_day, agent.id, 'bed'))
                return True
            else:
                # 加入等待队列
                heapq.heappush(self.queue, (day, agent.id))
                agent.in_queue = True
                agent.queue_start_time = day
                self.rejected_count += 1
                return False
    
    def request_test(self, agent: Agent, day: int) -> bool:
        """
        请求检测
        
        Args:
            agent: 个体Agent
            day: 当前天数
        
        Returns:
            是否成功检测
        """
        if len(self.test_queue) < self.params.testing_capacity:
            heapq.heappush(self.test_queue, (day + self.params.test_result_time, agent.id))
            return True
        else:
            return False
    
    def process_daily(self, day: int) -> Tuple[int, int]:
        """
        处理每日事件
        
        Args:
            day: 当前天数
        
        Returns:
            (出院人数, 检测完成人数)
        """
        discharged = 0
        tested = 0
        
        # 处理出院事件
        while self.discharge_events and self.discharge_events[0][0] <= day:
            discharge_day, agent_id, bed_type = heapq.heappop(self.discharge_events)
            if bed_type == 'icu':
                self.occupied_icu -= 1
            else:
                self.occupied_beds -= 1
            discharged += 1
        
        # 处理检测队列
        while self.test_queue and self.test_queue[0][0] <= day:
            test_day, agent_id = heapq.heappop(self.test_queue)
            tested += 1
        
        # 处理等待队列（如果有床位释放）
        while self.queue and self.occupied_beds < self.params.hospital_beds:
            queue_day, agent_id = heapq.heappop(self.queue)
            self.occupied_beds += 1
            # 重新安排出院事件
            wait_time = day - queue_day
            discharge_day = day + self.params.avg_hospital_stay + wait_time
            heapq.heappush(self.discharge_events, (discharge_day, agent_id, 'bed'))
        
        return discharged, tested


class HybridEpidemicModel:
    """混合仿真模型：ABM + SD + DES 三层耦合"""
    
    def __init__(self, population_size: int = 1000, 
                 seir_params: SEIRParams = None,
                 des_params: DESParams = None,
                 mosquito_params: MosquitoParams = None,
                 media_amplification: float = 1.0,
                 enable_info_behavior_feedback: bool = True,
                 enable_mosquito_transmission: bool = True):
        """
        初始化混合仿真模型
        
        Args:
            population_size: 人口规模
            seir_params: SEIR参数
            des_params: DES参数
            mosquito_params: 蚊媒参数
            media_amplification: 媒体放大系数
            enable_info_behavior_feedback: 是否启用信息-行为反馈
            enable_mosquito_transmission: 是否启用蚊媒传播（登革热特有）
        """
        self.population_size = population_size
        self.seir_params = seir_params or SEIRParams()
        self.des_params = des_params or DESParams()
        self.enable_info_behavior_feedback = enable_info_behavior_feedback
        self.enable_mosquito_transmission = enable_mosquito_transmission
        
        # 初始化Agent
        self.agents: List[Agent] = []
        for i in range(population_size):
            self.agents.append(Agent(id=i, state='S'))
        
        # 初始化子模型
        self.info_model = InformationSaliencyModel(media_amplification=media_amplification)
        self.risk_model = RiskPerceptionModel()
        self.behavior_model = BehaviorModel()
        self.hospital = HospitalDES(self.des_params)
        
        # 初始化蚊媒动态模型（登革热特有）
        if enable_mosquito_transmission:
            self.mosquito_model = MosquitoDynamicModel(mosquito_params or MosquitoParams())
        else:
            self.mosquito_model = None
        
        # 历史记录
        self.history: Dict[str, List] = {
            'day': [],
            'S': [], 'E': [], 'I': [], 'R': [],
            'info_saliency': [],
            'avg_risk': [],
            'avg_protection': [],
            'hospital_beds': [],
            'hospital_icu': [],
            'rejected': [],
            'effective_beta': [],
            'mosquito_risk': [],
            'infected_mosquitoes': []
        }
    
    def seed_infection(self, num_initial: int = 5):
        """
        种子感染
        
        Args:
            num_initial: 初始感染人数
        """
        infected_ids = np.random.choice(self.population_size, num_initial, replace=False)
        for agent_id in infected_ids:
            self.agents[agent_id].state = 'I'
    
    def step(self, day: int):
        """
        单步仿真
        
        Args:
            day: 当前天数
        """
        # 统计当前状态
        counts = {'S': 0, 'E': 0, 'I': 0, 'R': 0}
        for agent in self.agents:
            counts[agent.state] += 1
        
        # 更新信息显著性
        info_saliency = self.info_model.update(counts['I'], self.population_size, day)
        
        # 计算社会影响（周围人感染比例）
        social_influence = counts['I'] / self.population_size
        
        # 更新蚊媒动态（登革热特有）
        mosquito_risk = 0.0
        infected_mosquitoes = 0
        if self.enable_mosquito_transmission and self.mosquito_model:
            mosquito_risk = self.mosquito_model.update(counts['I'], day)
            infected_mosquitoes = self.mosquito_model.infected_mosquitoes
        
        # 第一遍：更新所有Agent的风险感知和防护行为
        for agent in self.agents:
            # 个人经历
            personal_experience = 1.0 if agent.state in ['E', 'I'] else 0.0
            
            # 更新风险感知
            if self.enable_info_behavior_feedback:
                self.risk_model.update_agent(agent, info_saliency, social_influence, personal_experience)
                self.behavior_model.update_protection(agent)
            else:
                agent.risk_perception = 0.0
                agent.protection_level = 0.0
        
        # 计算全人群平均防护水平（用于感染概率）
        total_protection = sum(agent.protection_level for agent in self.agents)
        avg_protection = total_protection / self.population_size
        # 修正：添加防护效率参数ε
        # 即使100%防护，仍有15%的残余传播风险
        effective_beta = self.seir_params.beta_base * (1 - self.seir_params.protection_efficiency * avg_protection)
        
        # 第二遍：状态转移（使用一致的平均防护水平）
        for agent in self.agents:
            # 状态转移
            if agent.state == 'S':
                # 感染概率（受人-人传播和蚊媒传播影响）
                human_transmission_prob = effective_beta * counts['I'] / self.population_size
                mosquito_transmission_prob = mosquito_risk if self.enable_mosquito_transmission else 0.0
                total_infection_prob = min(1.0, human_transmission_prob + mosquito_transmission_prob)
                
                if np.random.random() < total_infection_prob:
                    agent.state = 'E'
                    agent.exposed_day = day
            
            elif agent.state == 'E':
                # 潜伏期 -> 感染期
                agent.exposed_day += 1
                if np.random.random() < self.seir_params.sigma:
                    agent.state = 'I'
                    agent.infected_day = day
            
            elif agent.state == 'I':
                agent.infected_day += 1
                
                # 检测
                if not agent.detected and np.random.random() < self.seir_params.detection_rate:
                    agent.detected = True
                    self.hospital.request_test(agent, day)
                
                # 住院
                if not agent.hospital_admitted and np.random.random() < self.seir_params.hospitalization_rate:
                    severe = np.random.random() < 0.2  # 20%重症
                    self.hospital.request_admission(agent, day, severe)
                
                # 恢复
                if np.random.random() < self.seir_params.gamma:
                    agent.state = 'R'
        
        # 处理DES每日事件
        discharged, tested = self.hospital.process_daily(day)
        
        # 记录历史
        total_risk = sum(agent.risk_perception for agent in self.agents)
        avg_risk = total_risk / self.population_size
        
        self.history['day'].append(day)
        self.history['S'].append(counts['S'])
        self.history['E'].append(counts['E'])
        self.history['I'].append(counts['I'])
        self.history['R'].append(counts['R'])
        self.history['info_saliency'].append(info_saliency)
        self.history['avg_risk'].append(avg_risk)
        self.history['avg_protection'].append(avg_protection)
        self.history['hospital_beds'].append(self.hospital.occupied_beds)
        self.history['hospital_icu'].append(self.hospital.occupied_icu)
        self.history['rejected'].append(self.hospital.rejected_count)
        self.history['effective_beta'].append(effective_beta)
        self.history['mosquito_risk'].append(mosquito_risk)
        self.history['infected_mosquitoes'].append(infected_mosquitoes)
    
    def run(self, num_days: int = 200):
        """
        运行仿真
        
        Args:
            num_days: 仿真天数
        """
        for day in range(num_days):
            self.step(day)
    
    def get_results(self) -> pd.DataFrame:
        """
        获取结果DataFrame
        
        Returns:
            结果DataFrame
        """
        return pd.DataFrame(self.history)
