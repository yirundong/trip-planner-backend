"""高德地图MCP服务封装"""

from typing import List, Dict, Any, Optional
from hello_agents.tools import MCPTool
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

# 全局MCP工具实例
_amap_mcp_tool = None


def get_amap_mcp_tool() -> MCPTool:
    """
    获取高德地图MCP工具实例(单例模式)

    Returns:
        MCPTool实例
    """
    global _amap_mcp_tool

    if _amap_mcp_tool is None:
        settings = get_settings()

        if not settings.amap_api_key:
            raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")

        # 创建MCP工具
        _amap_mcp_tool = MCPTool(
            name="amap",
            description="高德地图服务,支持POI搜索、路线规划、天气查询等功能",
            server_command=["uvx", "amap-mcp-server"],
            env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
            auto_expand=True  # 自动展开为独立工具
        )

        print(f"✅ 高德地图MCP工具初始化成功")
        print(f"   工具数量: {len(_amap_mcp_tool._available_tools)}")

        # 打印可用工具列表
        if _amap_mcp_tool._available_tools:
            print("   可用工具:")
            for tool in _amap_mcp_tool._available_tools[:5]:  # 只打印前5个
                print(f"     - {tool.get('name', 'unknown')}")
            if len(_amap_mcp_tool._available_tools) > 5:
                print(f"     ... 还有 {len(_amap_mcp_tool._available_tools) - 5} 个工具")

    return _amap_mcp_tool


class AmapService:
    """高德地图服务封装类"""

    def __init__(self):
        """初始化服务"""
        self.mcp_tool = get_amap_mcp_tool()

    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """
        搜索POI

        Args:
            keywords: 搜索关键词
            city: 城市
            citylimit: 是否限制在城市范围内

        Returns:
            POI信息列表
        """
        try:
            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_text_search",
                "arguments": {
                    "keywords": keywords,
                    "city": city,
                    "citylimit": str(citylimit).lower()
                }
            })

            # 解析结果
            # 注意: MCP工具返回的是字符串,需要解析
            # 这里简化处理,实际应该解析JSON
            print(f"POI搜索结果: {result[:200]}...")  # 打印前200字符
            # 把原来的 print 替换成这三行，完全暴露原始数据
            # print("\n" + "🔥" * 20 + " 抓取到的完整原始数据 " + "🔥" * 20)
            # print(result)
            # print("🔥" * 50 + "\n")

            # TODO: 解析实际的POI数据   已解决
            import json
            import re

            # 1. 用正则精准抠出大括号里的 JSON 数据
            json_match = re.search(r'(\{.*\})', result, re.DOTALL)
            if not json_match:
                print("❌ 无法从结果中提取 JSON")
                return []

            data = json.loads(json_match.group(1))

            # 2. 拦截高德返回的网络报错
            if "error" in data:
                print(f"⚠️ MCP底层请求高德失败: {data['error']}")
                return []

            # 3. 提取核心的 pois 列表
            raw_pois = data.get("pois", [])
            if not isinstance(raw_pois, list):
                return []

            # 4. 数据清洗与模型组装 (极简版)
            parsed_results = []
            for item in raw_pois:
                try:
                    # 【核心过滤】只要不是风景名胜(11)或地名(19)开头的，直接过滤掉医院、停车场等噪音
                    typecode = item.get("typecode", "")
                    if not typecode.startswith(("11", "19")):
                        continue

                    # 【填坑】防范 address 偶尔是空列表 [] 的高德 Bug
                    raw_address = item.get("address", "")
                    address_str = "".join(raw_address) if isinstance(raw_address, list) else str(raw_address)

                    # 完美契合你的新模型，一行多余的代码都没有
                    poi = POIInfo(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        typecode=typecode,
                        address=address_str
                    )
                    parsed_results.append(poi)

                except Exception as e:
                    print(f"⚠️ 解析地点 '{item.get('name', '未知')}' 失败, 跳过。原因: {e}")

            print(f"✅ 成功提取并组装了 {len(parsed_results)} 个优质景点！")
            return parsed_results

        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []

    def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        查询天气

        Args:
            city: 城市名称

        Returns:
            天气信息列表
        """
        try:
            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_weather",
                "arguments": {
                    "city": city
                }
            })

            print(f"天气查询结果: {result[:200]}...")
            # 把原来的 print 替换成这三行，完全暴露原始数据
            # print("\n" + "🔥" * 20 + " 抓取到的完整原始数据 " + "🔥" * 20)
            # print(result)
            # print("🔥" * 50 + "\n")

            # TODO: 解析实际的天气数据   已解决
            import json
            import re

            # 1. 精准抠出大括号里的 JSON 数据
            json_match = re.search(r'(\{.*\})', result, re.DOTALL)
            if not json_match:
                print("❌ 无法从结果中提取 JSON")
                return []

            data = json.loads(json_match.group(1))

            # 2. 拦截高德返回的网络报错
            if "error" in data:
                print(f"⚠️ MCP底层请求高德天气失败: {data['error']}")
                return []

            # 3. 提取核心的天气预报列表
            # 注意：高德天气的数据核心在 "forecasts" 这个列表里
            forecasts = data.get("forecasts", [])
            if not isinstance(forecasts, list):
                return []

            # 4. 数据清洗与模型组装
            parsed_results = []
            for item in forecasts:
                try:
                    # 组装成你的 WeatherInfo 模型
                    # 高德分了白天和夜间的风向，这里为了适配你的模型，我们默认取白天的风向和风力
                    weather = WeatherInfo(
                        date=item.get("date", ""),
                        day_weather=item.get("dayweather", ""),
                        night_weather=item.get("nightweather", ""),
                        day_temp=item.get("daytemp", 0),
                        night_temp=item.get("nighttemp", 0),
                        wind_direction=item.get("daywind", ""),
                        wind_power=item.get("daypower", "")
                    )
                    parsed_results.append(weather)
                except Exception as e:
                    print(f"⚠️ 解析单日天气跳过: {e}")

            print(f"✅ 成功解析出 {len(parsed_results)} 天的天气预报！")
            return parsed_results


        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return []

    def plan_route(
            self,
            origin_address: str,
            destination_address: str,
            origin_city: Optional[str] = None,
            destination_city: Optional[str] = None,
            route_type: str = "walking"
    ) -> Dict[str, Any]:
        """
        规划路线

        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点城市
            destination_city: 终点城市
            route_type: 路线类型 (walking/driving/transit)

        Returns:
            路线信息
        """
        try:
            # 根据路线类型选择工具
            tool_map = {
                "walking": "maps_direction_walking_by_address",
                "driving": "maps_direction_driving_by_address",
                "transit": "maps_direction_transit_integrated_by_address"
            }

            tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")

            # 构建参数
            arguments = {
                "origin_address": origin_address,
                "destination_address": destination_address
            }

            # 公共交通需要城市参数
            if route_type == "transit":
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city
            else:
                # 其他路线类型也可以提供城市参数提高准确性
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city

            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": tool_name,
                "arguments": arguments
            })

            print(f"路线规划结果: {result[:200]}...")
            # 把原来的 print 替换成这三行，完全暴露原始数据
            # print("\n" + "🔥" * 20 + " 抓取到的完整原始数据 " + "🔥" * 20)
            # print(result)
            # print("🔥" * 50 + "\n")

            # TODO: 解析实际的路线数据  已解决
            import json
            import re

            # 3. 提取纯净 JSON
            json_match = re.search(r'(\{.*\})', result, re.DOTALL)
            if not json_match:
                return {}

            data = json.loads(json_match.group(1))
            if "error" in data:
                print(f"⚠️ 路线规划请求失败: {data['error']}")
                return {}

            # 4. 拆解高德路线包裹
            # 高德的核心数据藏得很深：route -> paths -> 第一个列表项
            route_data = data.get("route", {})
            paths = route_data.get("paths", [])

            if not paths:
                print("⚠️ 没找到可行路线")
                return {}

            first_path = paths[0]

            # 5. 提取距离和时间 (高德给的是字符串，最好转成数字类型)
            # 距离单位是米，时间单位是秒
            distance = float(first_path.get("distance", 0))
            duration = float(first_path.get("duration", 0))

            # 6. 生成一段人性化的路线描述 (提取前3步导航指令拼在一起)
            steps = first_path.get("steps", [])
            instructions = [step.get("instruction", "") for step in steps[:3]]
            description = "，".join(instructions) + "......" if instructions else "按导航路线行驶"

            # 7. 完美组装保安(RouteResponse)要求的 4 个字段
            final_result = {
                "distance": distance,
                "duration": duration,
                "route_type": route_type,
                "description": description
            }

            print(f"✅ 成功提取路线：距离 {distance}米，耗时 {duration}秒")
            return final_result


        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return {}

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        地理编码(地址转坐标)

        Args:
            address: 地址
            city: 城市

        Returns:
            经纬度坐标
        """
        try:
            arguments = {"address": address}
            if city:
                arguments["city"] = city

            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_geo",
                "arguments": arguments
            })

            print(f"地理编码结果: {result[:200]}...")
            # 把原来的 print 替换成这三行，完全暴露原始数据
            # print("\n" + "🔥" * 20 + " 抓取到的完整原始数据 " + "🔥" * 20)
            # print(result)
            # print("🔥" * 50 + "\n")

            # TODO: 解析实际的坐标数据  已解决
            import json
            import re

            # 2. 提取纯净 JSON
            json_match = re.search(r'(\{.*\})', result, re.DOTALL)
            if not json_match:
                return None

            data = json.loads(json_match.group(1))

            if "error" in data:
                print(f"⚠️ 地理编码请求失败: {data['error']}")
                return None

            # 3. 提取高德返回的坐标数据
            # 【关键修改】：根据真实数据，列表的名字是 "return"
            results_list = data.get("return", [])
            if not results_list:
                print(f"⚠️ 未找到地址 '{address}' 的坐标信息")
                return None

            # 取第一个匹配到的地址结果
            first_result = results_list[0]
            location_str = first_result.get("location", "")  # 例如: "116.397029,39.917839"

            # 4. 字符串切割与模型组装
            if location_str and "," in location_str:
                # 逗号前面是经度(lng)，后面是纬度(lat)
                lng_str, lat_str = location_str.split(",")

                # 完美塞进你的 Location 模型
                final_location = Location(
                    longitude=float(lng_str),
                    latitude=float(lat_str)
                )
                print(f"✅ 成功获取坐标: 经度 {final_location.longitude}, 纬度 {final_location.latitude}")
                return final_location

            return None

        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        获取POI详情

        Args:
            poi_id: POI ID

        Returns:
            POI详情信息
        """
        try:
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_search_detail",
                "arguments": {
                    "id": poi_id
                }
            })

            print(f"POI详情结果: {result[:200]}...")

            # 解析结果并提取图片
            import json
            import re

            # 尝试从结果中提取JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return {"raw": result}

        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}


# 创建全局服务实例
_amap_service = None


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service

    if _amap_service is None:
        _amap_service = AmapService()

    return _amap_service

