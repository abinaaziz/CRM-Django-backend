from django.contrib.contenttypes.models import ContentType 
from django.contrib.auth import get_user_model 
from django.db import transaction 
 
from rest_framework import serializers 
 
from .models import Note 
from apps.activities.activity.models import Activity 
 
 
User = get_user_model() 
 
 
class NoteSerializer(serializers.ModelSerializer): 
 
    # ================================================= 
    # INPUT ONLY 
    # ================================================= 
 
    sender_id = serializers.IntegerField( 
        write_only=True, 
        required=True 
    ) 
 
    module = serializers.CharField( 
        write_only=True, 
        required=True 
    ) 
 
    module_id = serializers.IntegerField( 
        write_only=True, 
        required=True 
    ) 
 
    # ================================================= 
    # OUTPUT ONLY 
    # ================================================= 
 
    created_by = serializers.SerializerMethodField( 
        read_only=True 
    ) 
 
    # ================================================= 
    # META 
    # ================================================= 
 
    class Meta: 
 
        model = Note 
 
        fields = [ 
            "id", 
            "created_by", 
 
            "sender_id", 
            "module", 
            "module_id", 
 
            "note", 
 
            "created_at", 
            "updated_at", 
        ] 
 
        read_only_fields = [ 
            "id", 
            "created_by", 
            "created_at", 
            "updated_at", 
        ] 
 
    # ================================================= 
    # VALIDATION 
    # ================================================= 
 
    def validate(self, attrs): 
 
        sender_id = attrs.get("sender_id") 
        module = attrs.get("module") 
        module_id = attrs.get("module_id") 
 
        # ================================================= 
        # SENDER 
        # ================================================= 
 
        if sender_id is None: 
 
            raise serializers.ValidationError({ 
                "sender_id": "This field is required." 
            }) 
 
        try: 
 
            sender = User.objects.get( 
                id=sender_id 
            ) 
 
        except User.DoesNotExist: 
 
            raise serializers.ValidationError({ 
                "sender_id": ( 
                    f"User with id {sender_id} " 
                    "does not exist." 
                ) 
            }) 
 
        # ================================================= 
        # MODULE 
        # ================================================= 
 
        if not module: 
 
            raise serializers.ValidationError({ 
                "module": "This field is required." 
            }) 
 
        module = module.lower().strip() 
 
        MODULE_MAP = { 
 
            "lead": ( 
                "leads", 
                "lead" 
            ), 
 
            "deal": ( 
                "deals", 
                "deal" 
            ), 
 
            "company": ( 
                "companies", 
                "company" 
            ), 
 
            "ticket": ( 
                "tickets", 
                "ticket" 
            ), 
        } 
 
        if module not in MODULE_MAP: 
 
            raise serializers.ValidationError({ 
                "module": ( 
                    "Invalid module. " 
                    "Allowed modules: " 
                    "lead, deal, company, ticket." 
                ) 
            }) 
 
        app_label, model_name = MODULE_MAP[module] 
 
        # ================================================= 
        # CONTENT TYPE 
        # ================================================= 
 
        try: 
 
            content_type = ContentType.objects.get( 
                app_label=app_label, 
                model=model_name 
            ) 
 
        except ContentType.DoesNotExist: 
 
            raise serializers.ValidationError({ 
                "module": ( 
                    f"{module} module does not exist." 
                ) 
            }) 
 
        # ================================================= 
        # MODULE ID 
        # ================================================= 
 
        if module_id is None: 
 
            raise serializers.ValidationError({ 
                "module_id": "This field is required." 
            }) 
 
        model_class = content_type.model_class() 
 
        if model_class is None: 
 
            raise serializers.ValidationError({ 
                "module": ( 
                    f"Could not find model " 
                    f"for '{module}'." 
                ) 
            }) 
 
        # ================================================= 
        # CHECK OBJECT 
        # ================================================= 
 
        if not model_class.objects.filter( 
            id=module_id 
        ).exists(): 
 
            raise serializers.ValidationError({ 
                "module_id": ( 
                    f"{module} with id " 
                    f"{module_id} does not exist." 
                ) 
            }) 
 
        # ================================================= 
        # STORE VALUES 
        # ================================================= 
 
        attrs["sender"] = sender 
        attrs["module"] = module 
        attrs["content_type"] = content_type 
        attrs["object_id"] = module_id 
 
        return attrs 
 
    # ================================================= 
    # CREATE 
    # ================================================= 
 
    @transaction.atomic 
    def create(self, validated_data): 
 
        sender = validated_data.pop( 
            "sender" 
        ) 
 
        validated_data.pop( 
            "module" 
        ) 
 
        content_type = validated_data.pop( 
            "content_type" 
        ) 
 
        object_id = validated_data.pop( 
            "object_id" 
        ) 
 
        validated_data.pop( 
            "sender_id", 
            None 
        ) 
 
        validated_data.pop( 
            "module_id", 
            None 
        ) 
 
        # ================================================= 
        # CREATE ACTIVITY 
        # ================================================= 
 
        activity = Activity.objects.create( 
            activity_type="note", 
            created_by=sender, 
            content_type=content_type, 
            object_id=object_id 
        ) 
 
        # ================================================= 
        # CREATE NOTE 
        # ================================================= 
 
        note = Note.objects.create( 
            activity=activity, 
            **validated_data 
        ) 
 
        return note 
 
    # ================================================= 
    # UPDATE 
    # ================================================= 
 
    def update( 
        self, 
        instance, 
        validated_data 
    ): 
 
        validated_data.pop( 
            "sender_id", 
            None 
        ) 
 
        validated_data.pop( 
            "module", 
            None 
        ) 
 
        validated_data.pop( 
            "module_id", 
            None 
        ) 
 
        validated_data.pop( 
            "sender", 
            None 
        ) 
 
        validated_data.pop( 
            "content_type", 
            None 
        ) 
 
        validated_data.pop( 
            "object_id", 
            None 
        ) 
 
        if "note" in validated_data: 
 
            # IMPORTANT: 
            # Keep HTML formatting exactly as 
            # received from the editor. 
            instance.note = validated_data["note"] 
 
            instance.save() 
 
        return instance 
 
    # ================================================= 
    # CREATED BY 
    # ================================================= 
 
    def get_created_by(self, obj): 
 
        if not obj.activity: 
            return None 
 
        user = obj.activity.created_by 
 
        if not user: 
            return None 
 
        name = user.get_full_name() 
 
        if not name: 
            name = user.email 
 
        return { 
            "id": user.id, 
            "name": name 
        } 
 
    # ================================================= 
    # OBJECT NAME 
    # ================================================= 
 
    def get_object_name( 
        self, 
        related_object 
    ): 
 
        # ================================================= 
        # LEAD 
        # ================================================= 
 
        if hasattr( 
            related_object, 
            "first_name" 
        ): 
 
            first_name = ( 
                getattr( 
                    related_object, 
                    "first_name", 
                    "" 
                ) or "" 
            ) 
 
            last_name = ( 
                getattr( 
                    related_object, 
                    "last_name", 
                    "" 
                ) or "" 
            ) 
 
            full_name = ( 
                f"{first_name} {last_name}" 
            ).strip() 
 
            if full_name: 
                return full_name 
 
        # ================================================= 
        # DEAL 
        # ================================================= 
 
        if hasattr( 
            related_object, 
            "deal_name" 
        ): 
 
            return related_object.deal_name 
 
        # ================================================= 
        # COMPANY 
        # ================================================= 
 
        if hasattr( 
            related_object, 
            "company_name" 
        ): 
 
            return related_object.company_name 
 
        # ================================================= 
        # NAME FALLBACK 
        # ================================================= 
 
        if hasattr( 
            related_object, 
            "name" 
        ): 
 
            return related_object.name 
 
        # ================================================= 
        # TICKET 
        # ================================================= 
 
        if hasattr( 
            related_object, 
            "title" 
        ): 
 
            return related_object.title 
 
        return str(related_object) 
 
    # ================================================= 
    # FINAL RESPONSE 
    # ================================================= 
 
    def to_representation( 
        self, 
        instance 
    ): 
 
        data = super().to_representation( 
            instance 
        ) 
 
        # ================================================= 
        # IMPORTANT 
        # ================================================= 
        # DO NOT use strip_tags() here. 
        # 
        # The editor sends HTML such as: 
        # 
        # <strong>Bold</strong> 
        # <em>Italic</em> 
        # <u>Underline</u> 
        # 
        # We must return that HTML to React so that 
        # NoteDetails can render the formatting. 
        # ================================================= 
 
        data["note"] = instance.note or "" 
 
        # ================================================= 
        # ACTIVITY 
        # ================================================= 
 
        activity = instance.activity 
 
        if not activity: 
            return data 
 
        content_type = activity.content_type 
 
        if not content_type: 
            return data 
 
        module = content_type.model.lower() 
 
        # ================================================= 
        # RELATED OBJECT 
        # ================================================= 
 
        model_class = content_type.model_class() 
 
        related_object = None 
 
        if model_class: 
 
            try: 
 
                related_object = model_class.objects.get( 
                    pk=activity.object_id 
                ) 
 
            except model_class.DoesNotExist: 
 
                related_object = None 
 
        # ================================================= 
        # MODULE 
        # ================================================= 
 
        data["module"] = module 
 
        # ================================================= 
        # MODULE DETAILS 
        # ================================================= 
 
        if related_object: 
 
            data[module] = { 
                "id": activity.object_id, 
                "name": self.get_object_name( 
                    related_object 
                ) 
            } 
 
        else: 
 
            data[module] = None 
 
        # ================================================= 
        # REMOVE INPUT FIELDS 
        # ================================================= 
 
        data.pop( 
            "sender_id", 
            None 
        ) 
 
        data.pop( 
            "module_id", 
            None 
        ) 
 
        # ================================================= 
        # FINAL RESPONSE 
        # ================================================= 
 
        response = {} 
 
        response["id"] = data.pop( 
            "id" 
        ) 
 
        response["created_by"] = data.pop( 
            "created_by" 
        ) 
 
        response["module"] = data.pop( 
            "module" 
        ) 
 
        response[module] = data.pop( 
            module 
        ) 
 
        response.update(data) 
 
        return response 