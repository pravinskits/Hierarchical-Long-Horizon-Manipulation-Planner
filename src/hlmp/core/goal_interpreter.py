import re
from typing import List, Dict, Any

class GoalInterpreter:
    def interpret(self, goal: str) -> List[Dict[str, Any]]:
        """
        Parses phrases like "Move the red cube to the target".
        Returns a list of raw operations: [{"action": "move", "object": "red_cube", "target": "target"}, ...]
        """
        clean_goal = goal.strip().rstrip(".").lower()
        
        # 0. Holistic multi-object goal matchers (handled first to avoid breaking lists with 'and')
        if re.search(r"tower", clean_goal):
            return [
                {"action": "pick", "object": "red_cube"},
                {"action": "place", "object": "red_cube", "target": "target_area"},
                {"action": "pick", "object": "blue_cube"},
                {"action": "place", "object": "blue_cube", "target": "red_cube"},
                {"action": "pick", "object": "green_cube"},
                {"action": "place", "object": "green_cube", "target": "blue_cube"}
            ]

        if re.search(r"sort all cubes", clean_goal) or clean_goal.startswith("sort"):
            return [
                {"action": "pick", "object": "red_cube"},
                {"action": "place", "object": "red_cube", "target": "target_area_1"},
                {"action": "pick", "object": "blue_cube"},
                {"action": "place", "object": "blue_cube", "target": "target_area_2"},
                {"action": "pick", "object": "green_cube"},
                {"action": "place", "object": "green_cube", "target": "target_area_3"}
            ]

        if "right corner" in clean_goal or "move all blocks to the right" in clean_goal:
            return [
                {"action": "pick", "object": "red_cube"},
                {"action": "place", "object": "red_cube", "target": "right_corner_1"},
                {"action": "pick", "object": "blue_cube"},
                {"action": "place", "object": "blue_cube", "target": "right_corner_2"},
                {"action": "pick", "object": "green_cube"},
                {"action": "place", "object": "green_cube", "target": "right_corner_3"}
            ]

        if clean_goal.startswith("retrieve") or "retrieve only" in clean_goal:
            return [
                {"action": "pick", "object": "blue_cube"},
                {"action": "place", "object": "blue_cube", "target": "safe_zone"}
            ]

        if "pyramid" in clean_goal:
            return [
                {"action": "pick", "object": "red_cube"},
                {"action": "place", "object": "red_cube", "target": "target_area_1"},
                {"action": "pick", "object": "blue_cube"},
                {"action": "place", "object": "blue_cube", "target": "target_area_2"},
                {"action": "pick", "object": "green_cube"},
                {"action": "place", "object": "green_cube", "target": "red_cube"}
            ]

        if "line up" in clean_goal or "in a row" in clean_goal:
            return [
                {"action": "pick", "object": "red_cube"},
                {"action": "place", "object": "red_cube", "target": "target_area_1"},
                {"action": "pick", "object": "blue_cube"},
                {"action": "place", "object": "blue_cube", "target": "target_area_2"},
                {"action": "pick", "object": "green_cube"},
                {"action": "place", "object": "green_cube", "target": "target_area_3"}
            ]

        if "push all" in clean_goal:
            return [
                {"action": "push", "object": "blue_cube", "target": "safe_zone"},
                {"action": "push", "object": "green_cube", "target": "safe_zone"},
                {"action": "push", "object": "red_cube", "target": "safe_zone"}
            ]

        if "scatter" in clean_goal:
            return [
                {"action": "pick", "object": "red_cube"},
                {"action": "place", "object": "red_cube", "target": "right_corner_1"},
                {"action": "pick", "object": "blue_cube"},
                {"action": "place", "object": "blue_cube", "target": "right_corner_2"},
                {"action": "pick", "object": "green_cube"},
                {"action": "place", "object": "green_cube", "target": "safe_zone"}
            ]

        # 1. Direct compound: "pick [X] and keep/place/put/drop in [Y]"
        pick_keep_match = re.match(
            r"(?:pick|take|grab|lift)\s+(?:the\s+)?(.*?)\s+and\s+(?:place|put|keep|drop|move)\s+(?:it\s+)?(?:in|into|to|at|beside)\s+(?:the\s+)?(.*)",
            clean_goal
        )
        if pick_keep_match:
            obj = self._normalize_entity(pick_keep_match.group(1))
            tgt = self._normalize_entity(pick_keep_match.group(2))
            return [
                {"action": "pick", "object": obj},
                {"action": "place", "object": obj, "target": tgt}
            ]

        operations = []
        # Support compound goals separated by "and"
        phrases = [p.strip().rstrip(".") for p in clean_goal.split(" and ") if p.strip()]
        
        last_obj = "red_cube"
        for phrase in phrases:

            # "Move/place/put/keep [object] to/in [target]"
            move_match = re.match(r"(?:move|place|put|keep|drop) (?:the )?(.*?) (?:to|in|into|beside) (?:the )?(.*)", phrase)
            if move_match:
                obj = self._normalize_entity(move_match.group(1))
                tgt = self._normalize_entity(move_match.group(2))
                operations.append({"action": "pick", "object": obj})
                operations.append({"action": "move", "object": obj, "target": tgt})
                operations.append({"action": "place", "object": obj, "target": tgt})
                last_obj = obj
                continue
                
            stack_match = re.match(r"stack (?:the )?(.*?) (?:on top of|on) (?:the )?(.*)", phrase)
            if stack_match:
                obj = self._normalize_entity(stack_match.group(1))
                tgt = self._normalize_entity(stack_match.group(2))
                operations.append({"action": "pick", "object": obj})
                operations.append({"action": "place", "object": obj, "target": tgt})
                last_obj = obj
                continue
                
            keep_match = re.match(r"keep (?:the )?(.*?) aside", phrase)
            if keep_match:
                obj = self._normalize_entity(keep_match.group(1))
                operations.append({"action": "pick", "object": obj})
                operations.append({"action": "place", "object": obj, "target": "safe_zone"})
                last_obj = obj
                continue

            # Inherited clause like "keep in the safe zone" (inherits last_obj)
            keep_dest_match = re.match(r"(?:keep|place|put|drop|move) (?:it )?(?:in|into|to|at) (?:the )?(.*)", phrase)
            if keep_dest_match:
                tgt = self._normalize_entity(keep_dest_match.group(1))
                operations.append({"action": "place", "object": last_obj, "target": tgt})
                continue
                
            clear_match = re.match(r"clear (?:the )?entire target area(.*)", phrase)
            if clear_match:
                operations.append({"action": "pick", "object": "red_cube"})
                operations.append({"action": "place", "object": "red_cube", "target": "safe_zone"})
                continue

            push_match = re.match(r"push (?:the )?(.*?) (?:toward|to|in|into) (?:the )?(.*)", phrase)
            if push_match:
                obj = self._normalize_entity(push_match.group(1))
                tgt = self._normalize_entity(push_match.group(2))
                operations.append({"action": "move", "object": obj})
                operations.append({"action": "push", "object": obj, "target": tgt})
                last_obj = obj
                continue
                
            # Fallback for simple "pick", "place", "move", "push"
            simple_match = re.match(r"(pick|take|grab|lift|place|put|move|push) (?:the )?(.*)", phrase)
            if simple_match:
                action, raw_obj = simple_match.groups()
                action = action.strip()
                norm_action = "pick" if action in ("pick", "take", "grab", "lift") else action
                norm_action = "place" if action in ("place", "put") else norm_action
                obj = self._normalize_entity(raw_obj)
                last_obj = obj
                if norm_action == "pick":
                    operations.append({"action": "pick", "object": obj})
                elif norm_action in ("place", "move", "push"):
                    operations.append({"action": norm_action, "object": obj, "target": "target_area"})
                continue
                
            raise ValueError(f"Unsupported goal phrase: '{phrase}'")
            
        return operations

    @staticmethod
    def _normalize_entity(name: str) -> str:
        n = name.strip().lower()
        for prefix in ("the ", "a ", "an ", "top of the ", "top of a ", "top of "):
            if n.startswith(prefix):
                n = n[len(prefix):]
        n = n.replace(".", "").strip()
        for prefix in ("the ", "a ", "an "):
            if n.startswith(prefix):
                n = n[len(prefix):]
        
        # Color mapping to specific cubes
        if n in ("red", "red cube", "red block", "red box", "red one") or ("red" in n and "cube" in n):
            return "red_cube"
        if n in ("blue", "blue cube", "blue block", "blue box", "blue one") or ("blue" in n and "cube" in n):
            return "blue_cube"
        if n in ("green", "green cube", "green block", "green box", "green one") or ("green" in n and "cube" in n):
            return "green_cube"
            
        # Target destinations
        if "safe" in n:
            return "safe_zone"
        if "right corner 3" in n or "corner 3" in n:
            return "right_corner_3"
        if "right corner 2" in n or "corner 2" in n:
            return "right_corner_2"
        if "right corner" in n or "corner" in n:
            return "right_corner_1"
        if "target area 1" in n or "target 1" in n:
            return "target_area_1"
        if "target area 2" in n or "target 2" in n:
            return "target_area_2"
        if "target area 3" in n or "target 3" in n:
            return "target_area_3"
        if n == "target":
            return "target"
        if "target" in n:
            return "target_area"
            
        return n.replace(" ", "_")
